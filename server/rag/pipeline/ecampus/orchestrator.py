"""
Agent orchestrator for personal/eCampus-backed queries. This is a SEPARATE
path from the existing RAG flow in aura_chat.py — it only runs when
intent_router.py classifies a query as needing live, person-specific data
(CGPA, attendance, fees, faculty schedule, etc.) rather than general
knowledge. General knowledge questions continue through the existing,
unmodified RAG pipeline in aura_chat.py.
"""

# TODO(unirp): Replace with UniRP endpoint — routes TBD. Do NOT implement any
# UniRP logic. Faculty personal-data tools routed through this orchestrator
# (get_faculty_schedule, and any future faculty ERP lookups) currently derive
# everything from eCampus/student-timetable aggregation and will need to call
# a UniRP-backed tool instead once routes are confirmed by IT.

import os
import json
from typing import Optional, List
from dotenv import load_dotenv

from ..key_manager import KeyManager
from .tool_registry import tools_for_role, TOOL_REGISTRY

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
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        # No self.client — every LLM call goes through KeyManager.call_with_rotation
        # so this orchestrator participates in key rotation just like every
        # other pipeline component.

    def _call_llm(self, messages: list, tools: Optional[list] = None, tool_choice: Optional[str] = None) -> object:
        """Single LLM call through KeyManager so daily-limit rotation applies here too."""
        model = self.model
        def _fn(client):
            kwargs: dict = {"model": model, "messages": messages}
            if tools:       kwargs["tools"] = tools
            if tool_choice: kwargs["tool_choice"] = tool_choice
            return client.chat.completions.create(**kwargs)
        return KeyManager.call_with_rotation(_fn, max_retries=3)

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
            for t in tools_for_role(role)
        ]

    def run(self, query: str, identity: dict, history: Optional[list] = None) -> dict:
        history = history or []
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
            tool = TOOL_REGISTRY.get(call.function.name)
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
                    result = tool.handler(identity, **args)
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
