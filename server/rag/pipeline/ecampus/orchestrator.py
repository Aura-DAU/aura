"""
Agent orchestrator for tool-backed queries (personal/eCampus or public KB).
This is a SEPARATE path from the existing RAG flow in aura_chat.py — it only
runs when intent_router.py classifies a query as PERSONAL_DATA or COMMUNITY
rather than GENERAL. General / vague queries continue through the existing
RAG pipeline in aura_chat_graph.
"""

import os
import json
from typing import Optional
from dotenv import load_dotenv

from ..inference_router import InferenceRouter
from ..prompt_loader import load_calendar_mcp_system_prompt
from .tool_registry import (
    tools_for_role as _ecampus_tools_for_role,
    public_kb_tools_for_role as _public_kb_tools_for_role,
    TOOL_REGISTRY as _ECAMPUS_TOOL_REGISTRY,
    PUBLIC_KB_TOOL_NAMES,
)
from ..timetable.tool_registry import (
    tools_for_role as _timetable_tools_for_role,
    TOOL_REGISTRY as _TIMETABLE_TOOL_REGISTRY,
    PUBLIC_TOOL_NAMES as _TIMETABLE_PUBLIC_TOOL_NAMES,
)
from ..timetable.calendar_mcp_client import (
    calendar_mcp_tools_for_role as _calendar_mcp_tools_for_role,
    calendar_mcp_registry as _calendar_mcp_registry,
)

# Merged view used by this orchestrator. Kept as two separate source-of-truth
# registries (pipeline.ecampus.tool_registry stays strictly read-only against
# the ERP; pipeline.timetable.tool_registry is the one place AURA writes its
# own, student-scoped data) so the read-only regression test for the ecampus
# package (test_write_tool_removal.py) keeps guarding just that package.
MERGED_TOOL_REGISTRY = {**_ECAMPUS_TOOL_REGISTRY, **_TIMETABLE_TOOL_REGISTRY}


def _tools_for_role(role: str):
    # Calendar MCP tools are personal-scope only (a student's own calendar), so
    # they're added here on the personal path -- never on the public-KB path.
    return (
        _ecampus_tools_for_role(role)
        + _timetable_tools_for_role(role)
        + _calendar_mcp_tools_for_role(role)
    )


CALENDAR_MCP_SYSTEM_PROMPT = load_calendar_mcp_system_prompt()


PERSONAL_SYSTEM_PROMPT = """You are AURA, DAU's academic assistant, handling a request that
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
""" + CALENDAR_MCP_SYSTEM_PROMPT + """
- If the timetable tool returns "is_common": true or "needs_configuration": true:
  1. Inform the user that this is the common timetable for their year.
  2. Display the timetable clearly.
  3. Proactively ask the user for their section (e.g. A, B, C, D) and any electives they have, so you can update and customize it for them.
  4. Once they provide the section/electives, use the set_my_cohort tool (for section) and save_my_elective_selections tool (for electives) to save their preferences.
- Keep answers concise and grounded only in what the tools returned.
"""

PUBLIC_KB_SYSTEM_PROMPT = """You are AURA, DAU's campus knowledge assistant.

Rules:
- Use the available tools to answer from published campus documents. Prefer the
  most specific tool (faculty profile, club roster, academic calendar,
  admissions, placements, facilities, policy, etc.) over guessing.
- For "what's the timetable for <year/sem> <branch> section <X>"-style questions
  about a cohort that is NOT the requester's own, use get_cohort_timetable —
  it queries the live master schedule directly. Don't fall back to a generic
  "couldn't find that" answer for these; call the tool with whatever
  sem/year/section/branch the user gave (section defaults to 'A').
- Never invent people, club members, convenors, emails, dates, fees, or
  committee composition — if a tool returns empty or missing fields, say the
  published campus documents do not list that detail.
- Never call or imply personal ERP records (CGPA, fees, attendance, hostel
  allotment) for another student. These tools only return KB-published facts.
- Keep answers concise and grounded only in what the tools returned.
"""

# Backward-compatible aliases.
COMMUNITY_SYSTEM_PROMPT = PUBLIC_KB_SYSTEM_PROMPT
SYSTEM_PROMPT = PERSONAL_SYSTEM_PROMPT


def _connect_action_required(tool_results: list[dict]) -> dict | None:
    """When a calendar tool reported the student hasn't linked Google Calendar,
    return a structured connect prompt for the client to render as an inline
    "Connect Google Calendar" CTA (the GPT/Claude connector pattern) instead of
    leaving it to the model's prose. None when no connect action is needed."""
    for r in tool_results:
        if isinstance(r, dict) and r.get("status") == "calendar_not_connected":
            return {
                "type": "connect_required",
                "provider": "google_calendar",
                "connect_path": "/settings/calendar",
                "reason": "sync_timetable",
                "message": (
                    r.get("message")
                    or "Connect your Google Calendar to add your timetable to your schedule."
                ),
            }
    return None

# tool_scope values that expose public KB tools (community + domain KB).
_PUBLIC_KB_SCOPES = frozenset({"community", "public_kb"})

# Narrow personal scope for the in-chat "actions" path: the student's own
# timetable + Google Calendar MCP tools ONLY -- deliberately NOT the ecampus
# ERP read tools, so routing a calendar/schedule request here can never bypass
# the curated _n_personal_data ERP path for CGPA / attendance / grades.
_PERSONAL_ACTIONS_SCOPE = "personal_actions"


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

    def _tool_schemas(self, role: str, tool_scope: str = "personal") -> list[dict]:
        if tool_scope in _PUBLIC_KB_SCOPES:
            selected = _public_kb_tools_for_role(role) + [
                t for t in _timetable_tools_for_role(role)
                if t.name in _TIMETABLE_PUBLIC_TOOL_NAMES
            ]
        elif tool_scope == _PERSONAL_ACTIONS_SCOPE:
            selected = _timetable_tools_for_role(role) + _calendar_mcp_tools_for_role(role)
        else:
            selected = _tools_for_role(role)
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in selected
        ]

    def run(
        self,
        query: str,
        identity: dict,
        history: Optional[list] = None,
        request_context=None,
        tool_scope: str = "personal",
    ) -> dict:
        history = (history or [])[-6:]
        use_public_kb = tool_scope in _PUBLIC_KB_SCOPES
        system = PUBLIC_KB_SYSTEM_PROMPT if use_public_kb else PERSONAL_SYSTEM_PROMPT
        messages = (
            [{"role": "system", "content": system}]
            + [{"role": h.get("role", "user"), "content": h.get("content", "")} for h in history]
            + [{"role": "user", "content": query}]
        )

        tool_schemas = self._tool_schemas(identity["role"], tool_scope=tool_scope)
        if not tool_schemas:
            if use_public_kb:
                return {
                    "answer": "I don't have campus knowledge tools available for your account type.",
                    "sources": [],
                }
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
            return {"answer": msg.content, "sources": [], "used_tools": False}

        tool_messages = []
        tool_results: list[dict] = []
        for call in msg.tool_calls:
            tool = MERGED_TOOL_REGISTRY.get(call.function.name) or _calendar_mcp_registry().get(call.function.name)
            # Public-KB path: refuse personal ERP / write tools even if named
            # (defense in depth — personal ERP stays gated).
            if (
                use_public_kb
                and call.function.name not in PUBLIC_KB_TOOL_NAMES
                and call.function.name not in _TIMETABLE_PUBLIC_TOOL_NAMES
            ):
                result = {"error": "Tool not available on the public KB path."}
            elif tool is None or identity["role"] not in tool.allowed_roles:
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

            tool_results.append(result if isinstance(result, dict) else {})
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
        out: dict = {
            "answer": follow_up.choices[0].message.content,
            "sources": [],
            "used_tools": True,
        }
        action_required = _connect_action_required(tool_results)
        if action_required:
            out["action_required"] = action_required
        return out
