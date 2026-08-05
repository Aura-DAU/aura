"""
Agent orchestrator for tool-backed queries (personal/eCampus or public KB).
This is a SEPARATE path from the existing RAG flow in aura_chat.py — it only
runs when intent_router.py classifies a query as PERSONAL_DATA or COMMUNITY
rather than GENERAL. General / vague queries continue through the existing
RAG pipeline in aura_chat_graph.
"""

import os
import json
import logging
import re
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

logger = logging.getLogger(__name__)

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
- The requester's own weekly class timetable IS available to you. For any
  phrasing of "my timetable" / "my time table" / "my schedule" / "what
  classes do I have today/tomorrow", call get_my_timetable and answer from
  its rows (faculty: get_my_teaching_schedule). Never tell the user you
  cannot access their timetable, and never redirect them to the university
  portal for it.
- If get_my_timetable errors or returns no classes, say their timetable
  couldn't be loaded, then offer the concrete next step: confirm their
  section (set_my_cohort) and electives (save_my_elective_selections), or
  link their account if a tool asked for that.
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


def _confirmation_action_required(tool_results: list[dict]) -> dict | None:
    """When a calendar tool returned a preview that awaits the student's
    go-ahead (status "confirmation_required"), return a structured confirmation
    prompt for the client to render as an inline Confirm button — the same
    pattern as _connect_action_required. The click still travels back as a
    normal "confirm" chat message, so the confirmation regex gate
    (_CONFIRMATION_RE / _CALENDAR_CONFIRMATION_CONTEXT_RE) is untouched.
    None when nothing awaits confirmation."""
    for r in tool_results:
        if isinstance(r, dict) and r.get("status") == "confirmation_required":
            action: dict = {
                "type": "confirmation_required",
                "provider": "google_calendar",
                "action": "sync_timetable",
                "message": _phrase_calendar_result("preview_timetable_sync", r),
            }
            count = r.get("class_count")
            if isinstance(count, int):
                action["event_count"] = count
            return action
    return None


def _phrase_calendar_result(tool_name: str, result: dict) -> str:
    """Deterministic, user-facing phrasing for a calendar tool result.

    The deterministic calendar path (see EcampusOrchestrator._run_calendar_tool)
    does not route the tool result back through the model, so the answer is built
    here instead. This guarantees two things a paraphrasing LLM turn does not:
    the request never degrades to a generic "I can't access your calendar"
    refusal, and a preview always ends with the "Google Calendar ... proceed"
    phrasing that the confirmation gate (_CALENDAR_CONFIRMATION_CONTEXT_RE) keys
    on, so the follow-up "yes" reliably triggers the sync."""
    message = result.get("message")
    status = result.get("status")

    if status == "calendar_not_connected":
        return message or (
            "Your Google Calendar isn't connected for writing yet. Connect it "
            "from Settings > Calendar, then ask me to sync your timetable again."
        )
    if "error" in result:
        return (
            "I couldn't complete that Google Calendar action just now. "
            "Please try again in a moment."
        )

    if tool_name == "calendar_status":
        if result.get("calendar_linked"):
            return (
                "Your Google Calendar is connected. Ask me to sync your timetable "
                "to it whenever you like."
            )
        return (
            "Your Google Calendar isn't connected yet. Connect it from "
            "Settings > Calendar, then ask me to sync your timetable."
        )
    if tool_name == "preview_timetable_sync":
        if message:
            return message
        count = result.get("class_count", 0)
        return (
            f"This will create or update {count} recurring weekly events on your "
            "Google Calendar — one per class. Confirm to proceed."
        )
    if tool_name == "sync_timetable_to_calendar":
        if status == "synced":
            created = result.get("created", 0)
            updated = result.get("updated", 0)
            removed = result.get("removed", 0)
            return (
                f"Done — your timetable is synced to Google Calendar "
                f"({created} created, {updated} updated, {removed} removed)."
            )
        return message or "Your timetable sync to Google Calendar has started."
    if tool_name == "unsync_timetable_from_calendar":
        removed = result.get("removed", 0)
        return (
            f"Removed {removed} timetable event(s) that AURA had added to your "
            "Google Calendar."
        )
    return message or "Done."


# tool_scope values that expose public KB tools (community + domain KB).
_PUBLIC_KB_SCOPES = frozenset({"community", "public_kb"})

# Narrow personal scope for the in-chat "actions" path: the student's own
# timetable + Google Calendar MCP tools ONLY -- deliberately NOT the ecampus
# ERP read tools, so routing a calendar/schedule request here can never bypass
# the curated _n_personal_data ERP path for CGPA / attendance / grades.
_PERSONAL_ACTIONS_SCOPE = "personal_actions"

_CALENDAR_STATUS_RE = re.compile(
    r"\b(?:calendar\s+status|(?:calendar|it)\s+(?:is\s+)?(?:connected|linked)|"
    r"(?:is|has)\s+(?:my\s+)?(?:google\s+)?calendar\s+(?:connected|linked))\b",
    re.IGNORECASE,
)
_CALENDAR_SYNC_RE = re.compile(
    r"\b(?:add|sync|put|export|save)\b.{0,40}\b(?:calendar|schedule|time\s*table|classes?)\b"
    r"|\b(?:schedule|time\s*table|classes?)\b.{0,30}\bcalendar\b",
    re.IGNORECASE,
)
_TIMETABLE_SYNC_DETAILS_CONTEXT_RE = re.compile(
    r"\bsync(?:ing)?\b.{0,80}\btime\s*table\b.{0,120}\b(?:section|elective)\b",
    re.IGNORECASE | re.DOTALL,
)
_TIMETABLE_DETAILS_FETCH_RE = re.compile(
    r"^\s*(?:please\s+)?(?:fetch|get|read|use|take)\b.{0,40}"
    r"\b(?:from\s+)?(?:my\s+)?time\s*table\b[\s.!?]*$",
    re.IGNORECASE,
)
_TIMETABLE_EDIT_RE = re.compile(
    r"\b(?:change|edit|update|move|reschedule|shift|remove|delete|cancel|undo|revert)\b"
    r".{0,60}\b(?:my\s+)?(?:timetable|schedule|class|lecture|lab|tutorial)\b"
    r"|\b(?:my\s+)?(?:timetable|schedule|class|lecture|lab|tutorial)\b.{0,60}"
    r"\b(?:change|edit|update|move|reschedule|shift|remove|delete|cancel|undo|revert)\b"
    r"|\badd\b.{0,60}\b(?:class|lecture|lab|tutorial)\b",
    re.IGNORECASE,
)
_TIMETABLE_EDIT_RE = re.compile(
    r"\b(?:change|edit|update|move|reschedule|shift|remove|delete|cancel|undo|revert)\b"
    r".{0,60}\b(?:my\s+)?(?:timetable|schedule|class|lecture|lab|tutorial)\b"
    r"|\b(?:my\s+)?(?:timetable|schedule|class|lecture|lab|tutorial)\b.{0,60}"
    r"\b(?:change|edit|update|move|reschedule|shift|remove|delete|cancel|undo|revert)\b"
    r"|\badd\b.{0,60}\b(?:class|lecture|lab|tutorial)\b",
    re.IGNORECASE,
)
_CONFIRMATION_RE = re.compile(
    r"^\s*(?:yes|yep|yeah|confirm(?:ed)?|proceed|go ahead|do it|please do|sync it)"
    r"[\s.!]*$",
    re.IGNORECASE,
)
_CALENDAR_CONFIRMATION_CONTEXT_RE = re.compile(
    r"\bgoogle calendar\b.*\b(?:confirm|proceed)\b"
    r"|\b(?:confirm|proceed)\b.*\bgoogle calendar\b",
    re.IGNORECASE | re.DOTALL,
)
# A remove/unsync request (e.g. "delete my timetable from my calendar"). Kept
# separate from _CALENDAR_SYNC_RE because that pattern's "timetable ... calendar"
# arm also matches a *removal* phrasing -- unsync must win, so it is checked
# first and the sync arm never sees a removal request.
_CALENDAR_UNSYNC_RE = re.compile(
    r"\b(?:unsync|remove|delete|clear|wipe)\b.{0,40}"
    r"\b(?:calendar|timetable|classes?|schedule|events?)\b"
    r"|\b(?:calendar|timetable|classes?|schedule)\b.{0,30}"
    r"\b(?:unsync|remove|delete|clear|wipe)\b",
    re.IGNORECASE,
)
# The confirmation context for a *removal*. The unsync confirmation prompt also
# contains "...Google Calendar... proceed", so the sync context would otherwise
# swallow it -- this is checked first and keys on the removal verb the sync
# preview prompt never contains.
_CALENDAR_UNSYNC_CONFIRMATION_CONTEXT_RE = re.compile(
    r"\b(?:remove|delete|unsync|clear)\b.*\b(?:google\s+)?calendar\b"
    r"|\b(?:google\s+)?calendar\b.*\b(?:remove|delete|unsync|clear)\b",
    re.IGNORECASE | re.DOTALL,
)
_TIMETABLE_EDIT_CONFIRMATION_CONTEXT_RE = re.compile(
    r"\b(?:timetable|schedule|class|lecture|lab|tutorial)\b.*\b(?:confirm|apply|proceed)\b"
    r"|\b(?:confirm|apply|proceed)\b.*\b(?:timetable|schedule|class|lecture|lab|tutorial)\b",
    re.IGNORECASE | re.DOTALL,
)


def _is_timetable_edit_intent(query: str) -> bool:
    """Recognise changes to AURA's personal timetable, not calendar export."""
    return bool(_TIMETABLE_EDIT_RE.search(query))


def _is_timetable_edit_confirmation(query: str, history: list[dict]) -> bool:
    if not _CONFIRMATION_RE.fullmatch(query):
        return False
    previous_assistant = next(
        (
            str(turn.get("content", ""))
            for turn in reversed(history)
            if turn.get("role") == "assistant"
        ),
        "",
    )
    return bool(
        _TIMETABLE_EDIT_CONFIRMATION_CONTEXT_RE.search(previous_assistant)
        and not _CALENDAR_CONFIRMATION_CONTEXT_RE.search(previous_assistant)
    )


def _is_calendar_unsync_intent(query: str) -> bool:
    """True for a request to remove AURA's timetable events from the calendar.

    A removal is a write, so it is never dispatched directly: the graph emits a
    confirmation prompt first (see _n_personal_tools) and the follow-up "yes"
    reaches the unsync tool through _required_calendar_tool's confirmation arm."""
    if _is_timetable_edit_intent(query) and not re.search(
        r"\b(?:from|off)\b.{0,30}\b(?:google\s+)?calendar\b",
        query,
        re.IGNORECASE,
    ):
        return False
    return bool(_CALENDAR_UNSYNC_RE.search(query))


def _required_calendar_tool(query: str, history: list[dict]) -> str | None:
    """Pin supported calendar intents to their MCP tool.

    Prompt-only tool selection is not reliable enough here: if the model emits
    prose instead of a tool call, the graph falls back to the personal-data
    responder. An explicit sync request is itself authorization to update the
    signed-in student's calendar; destructive unsync requests still require a
    separate confirmation.
    """
    if _CONFIRMATION_RE.fullmatch(query):
        previous_assistant = next(
            (
                str(turn.get("content", ""))
                for turn in reversed(history)
                if turn.get("role") == "assistant"
            ),
            "",
        )
        # Removal is checked before sync: the unsync prompt matches both
        # contexts, so sync would otherwise win and add events instead.
        if _CALENDAR_UNSYNC_CONFIRMATION_CONTEXT_RE.search(previous_assistant):
            return "unsync_timetable_from_calendar"
        if _CALENDAR_CONFIRMATION_CONTEXT_RE.search(previous_assistant):
            return "sync_timetable_to_calendar"

    if _CALENDAR_STATUS_RE.search(query):
        return "calendar_status"

    previous_assistant = next(
        (
            str(turn.get("content", ""))
            for turn in reversed(history)
            if turn.get("role") == "assistant"
        ),
        "",
    )
    if (
        _TIMETABLE_DETAILS_FETCH_RE.fullmatch(query)
        and _TIMETABLE_SYNC_DETAILS_CONTEXT_RE.search(previous_assistant)
    ):
        return "sync_timetable_to_calendar"

    # Timetable edits use update_my_timetable. They may contain words such as
    # "add", "remove", or "schedule", which also occur in calendar requests;
    # keep them out of the deterministic calendar tool path.
    if _is_timetable_edit_intent(query):
        return None
    # A first-time removal request is not dispatched here (no tool returned): the
    # graph asks for confirmation, and the "yes" hits the confirmation arm above.
    # Returning None -- rather than falling through to the sync arm, whose regex
    # also matches "remove ... timetable ... calendar" -- is what stops an
    # unconfirmed request from ever deleting events.
    if _CALENDAR_UNSYNC_RE.search(query):
        return None
    if _CALENDAR_SYNC_RE.search(query):
        return "sync_timetable_to_calendar"
    return None


class EcampusOrchestrator:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv("VLLM_MODEL", os.getenv("GROQ_MODEL", "Qwen/Qwen3-32B-AWQ"))
        # No self.client — every LLM call goes through InferenceRouter.call_with_rotation
        # so this orchestrator participates in key rotation just like every
        # other pipeline component.

    def _call_llm(
        self,
        messages: list,
        tools: Optional[list] = None,
        tool_choice: Optional[str | dict] = None,
    ) -> object:
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

        required_tool = (
            _required_calendar_tool(query, history)
            if tool_scope == _PERSONAL_ACTIONS_SCOPE
            else None
        )

        # Deterministic calendar path: the intent gate has already decided
        # exactly which calendar tool to run, and every calendar tool takes zero
        # model-chosen arguments (erp_id is injected from the verified identity).
        # So run it ourselves rather than asking the model to emit a tool call --
        # a self-hosted model that ignores a forced tool_choice would otherwise
        # answer in prose, and the request would silently degrade to a generic
        # "I can't access your calendar" refusal. This is what lets the agent act
        # on Google Calendar autonomously whenever a student asks, on any model.
        if required_tool:
            return self._run_calendar_tool(required_tool, identity)

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

                if call.function.name in ("update_my_timetable", "save_my_elective_selections", "set_my_cohort"):
                    args.pop("confirm", None)  # Strip out any hallucinated confirmation
                    if _is_timetable_edit_confirmation(query, history):
                        args["confirm"] = True

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
        action_required = _connect_action_required(
            tool_results
        ) or _confirmation_action_required(tool_results)
        if action_required:
            out["action_required"] = action_required
        return out

    def _run_calendar_tool(self, tool_name: str, identity: dict) -> dict:
        """Execute a decided calendar MCP tool directly and phrase the result.

        No LLM tool-calling is involved: the tool name is fixed by the intent
        gate and the tool takes no model-chosen arguments (erp_id is injected by
        the MCP adapter from the verified identity). The trust boundary is
        unchanged -- the model never picks whose calendar is touched. Returns the
        same {answer, sources, used_tools[, action_required]} shape the
        model-driven path returns, so _n_personal_tools consumes it identically."""
        tool = _calendar_mcp_registry().get(tool_name)
        if tool is None or identity["role"] not in tool.allowed_roles:
            # Discovery failed (MCP unreachable) or the role isn't allowed. Not
            # used_tools, so _n_personal_tools falls through to the curated path.
            return {"answer": "", "sources": [], "used_tools": False}

        try:
            result = tool.handler(identity)
        except Exception as e:  # noqa: BLE001 -- surfaced as a soft calendar error
            logger.exception("Calendar MCP tool %s raised", tool_name)
            result = {"error": str(e)}
        if not isinstance(result, dict):
            result = {}
        if "error" in result:
            # _phrase_calendar_result turns this into a generic "try again"
            # answer; keep the real cause visible in server logs.
            logger.error("Calendar MCP tool %s errored: %s", tool_name, result["error"])

        out: dict = {
            "answer": _phrase_calendar_result(tool_name, result),
            "sources": [],
            "used_tools": True,
        }
        action_required = _connect_action_required(
            [result]
        ) or _confirmation_action_required([result])
        if action_required:
            out["action_required"] = action_required
        return out
