"""
Agent orchestrator for personal/eCampus-backed queries. This is a SEPARATE
path from the existing RAG flow in aura_chat.py — it only runs when
intent_router.py classifies a query as needing live, person-specific data
(CGPA, attendance, fees, faculty schedule, etc.) rather than general
knowledge. General knowledge questions continue through the existing,
unmodified RAG pipeline in aura_chat.py.
"""

import os
import json
from typing import Optional, List
from dotenv import load_dotenv

from ..inference_router import InferenceRouter
from .tool_registry import tools_for_role as _ecampus_tools_for_role, TOOL_REGISTRY as _ECAMPUS_TOOL_REGISTRY
from ..timetable.tool_registry import tools_for_role as _timetable_tools_for_role, TOOL_REGISTRY as _TIMETABLE_TOOL_REGISTRY

# Merged view used by this orchestrator. Kept as two separate source-of-truth
# registries (pipeline.ecampus.tool_registry stays strictly read-only against
# the ERP; pipeline.timetable.tool_registry is the one place AURA writes its
# own, student-scoped data) so the read-only regression test for the ecampus
# package (test_write_tool_removal.py) keeps guarding just that package.
MERGED_TOOL_REGISTRY = {**_ECAMPUS_TOOL_REGISTRY, **_TIMETABLE_TOOL_REGISTRY}


def _tools_for_role(role: str):
    return _ecampus_tools_for_role(role) + _timetable_tools_for_role(role)

SYSTEM_PROMPT = """You are AURA, DAU's academic assistant, handling a request that
needs the requester's own live academic data (or, for faculty, data a student has
explicitly shared with them).

Rules:
- Use the available tools to answer. Never invent CGPA, attendance, grades, or any
  other personal data — if no tool can answer the question, say so plainly.
- A tool returning {"action_needed": "link_ecampus_account"} means the user hasn't
  connected their eCampus account yet — tell them that directly and clearly,
  don't make up an answer instead.
- A tool returning {"action_needed": "student_consent_required"} means the
  requested student hasn't shared their data with this faculty member — tell
  them that, don't imply the data doesn't exist.
- For any tool whose category is "write" (sharing data, applying for things,
  clearing cache), you must get the user's explicit confirmation before it
  executes. The orchestrator will return a confirmation prompt instead of a
  result on the first attempt — relay that prompt to the user as-is.
- Keep answers concise and grounded only in what the tools returned.
"""


class EcampusOrchestrator:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv("VLLM_MODEL", os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ"))
        # No self.client — every LLM call goes through InferenceRouter.call_with_rotation
        # so this orchestrator participates in key rotation just like every
        # other pipeline component.

    def _call_llm(self, messages: list, tools: Optional[list] = None, tool_choice: Optional[str] = None) -> object:
        """Single LLM call through InferenceRouter so node failover applies here too."""
        model = self.model
        def _fn(client):
            kwargs: dict = {"model": model, "messages": messages}
            if tools:       kwargs["tools"] = tools
            if tool_choice: kwargs["tool_choice"] = tool_choice
            return client.chat.completions.create(**kwargs)
        return InferenceRouter.call_with_rotation(_fn, max_retries=3)

    def _tool_schemas(self, role: str) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in _tools_for_role(role)
        ]

    def run(self, query: str, identity: dict, history: Optional[list] = None, request_context=None) -> dict:
        history = (history or [])[-6:]
        messages = (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + [{"role": h.get("role", "user"), "content": h.get("content", "")} for h in history]
            + [{"role": "user", "content": query}]
        )

        tool_schemas = self._tool_schemas(identity["role"])
        if not tool_schemas:
            return {
                "answer": "I don't have any personal-data tools available for your account type.",
                "sources": [],
            }

        response = self._call_llm(
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            return {"answer": msg.content, "sources": []}

        tool_messages = []
        for call in msg.tool_calls:
            tool = MERGED_TOOL_REGISTRY.get(call.function.name)
            if tool is None or identity["role"] not in tool.allowed_roles:
                # Defense in depth: even if the model somehow names a tool it
                # wasn't given a schema for, refuse rather than execute it.
                result = {"error": "Tool not available for this account type."}
            else:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}
                try:
                    result = tool.handler(identity, request_context=request_context, **args)
                except TypeError as exc:
                    if "unexpected keyword argument 'request_context'" in str(exc):
                        result = tool.handler(identity, **args)
                    else:
                        raise
                except Exception as e:
                    result = {"error": str(e)}

            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str),
            })

        follow_up = self._call_llm(
            messages=messages + [
                {"role": "assistant", "content": msg.content, "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in msg.tool_calls
                ]},
                *tool_messages,
            ],
        )
        return {"answer": follow_up.choices[0].message.content, "sources": []}
