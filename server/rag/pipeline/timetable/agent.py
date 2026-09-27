"""
Tool-calling agent for the requester's own timetable and Google Calendar.

This is the only tool-calling path left in the chat graph. It never answers
general university questions: those always go through the grounded RAG
pipeline. A model reply that did not call a tool is reported as
used_tools=False so the graph never shows ungrounded prose to the user.
"""

import json
import logging
import os
import re
from typing import Any, Optional

from dotenv import load_dotenv

from ..inference_router import InferenceRouter
from ..prompt_loader import load_calendar_mcp_system_prompt
from .tool_registry import (
    PUBLIC_TOOL_NAMES as TIMETABLE_PUBLIC_TOOL_NAMES,
    TOOL_REGISTRY as TIMETABLE_TOOL_REGISTRY,
    tools_for_role as timetable_tools_for_role,
)
from .calendar_mcp_client import (
    calendar_mcp_registry,
    calendar_mcp_tools_for_role,
)
from personal_query_classifier import PUBLIC_PROGRAMME_OVERRIDE_PAT

logger = logging.getLogger(__name__)

# Tool names whose successful result means the requester's own timetable
# changed, so the frontend must refetch /api/timetable/me. Elective and cohort
# changes count because they change which master rows apply to the student.
TIMETABLE_MUTATING_TOOL_NAMES = {
    "update_my_timetable",
    "undo_timetable_change",
    "set_my_cohort",
    "save_my_elective_selections",
}

# Agent completions are short (a timetable listing or a confirmation).
_AGENT_MAX_TOKENS = int(os.getenv("AURA_AGENT_MAX_TOKENS", "900"))

CALENDAR_MCP_SYSTEM_PROMPT = load_calendar_mcp_system_prompt()

PERSONAL_SYSTEM_PROMPT = """You are AURA, DAU's academic assistant, handling a request about the
requester's own class timetable or Google Calendar.

Rules:
- Use the available tools to answer. Never invent classes, rooms, times or
  course codes; if no tool can answer the question, say so plainly.
- For any phrasing of "my timetable" / "my schedule" / "what classes do I have
  today/tomorrow", call get_my_timetable (faculty: get_my_teaching_schedule)
  and answer only from its rows.
- If get_my_timetable errors or returns no classes, say the timetable couldn't
  be loaded, then offer the next step: confirm the section (set_my_cohort) and
  electives (save_my_elective_selections).
- Write tools return a confirmation prompt on the first attempt; relay that
  prompt to the user as-is.
- Students may describe a timetable addition as
    Course ID -
    Days -
    Time -
  Parse it and call update_my_timetable with the equivalent fields.
""" + CALENDAR_MCP_SYSTEM_PROMPT + """
- If the timetable tool returns "is_common": true or "needs_configuration": true:
  1. Say this is the common timetable for their year.
  2. Display the timetable clearly.
  3. Ask for their section (e.g. A, B, C, D) and electives so you can customize it.
  4. Once given, call set_my_cohort (section) and save_my_elective_selections (electives).
- Keep answers concise and grounded only in what the tools returned.
"""

PUBLIC_TIMETABLE_SYSTEM_PROMPT = """You are AURA, DAU's academic assistant, looking up the published
class timetable of a named cohort.

Rules:
- Call get_cohort_timetable with the semester/year, section and branch the user
  named (section defaults to 'A').
- Answer only from the rows the tool returned. Never invent classes, rooms or
  times; if the tool returns nothing, say the timetable for that cohort is not
  available.
- Keep answers concise.
"""

# Scopes the graph can request.
SCOPE_PERSONAL = "personal"                  # own timetable reads + writes + calendar
SCOPE_PERSONAL_ACTIONS = "personal_actions"  # same tool set, entered from the action gate
SCOPE_PUBLIC_TIMETABLE = "public_timetable"  # a named cohort's published timetable

_CONNECT_THEN_SYNC_MESSAGE = (
    "Connect your Google Calendar to sync your timetable. "
    "After you connect, I'll sync your classes automatically."
)

# ── Deterministic routing patterns ──────────────────────────────────────────

# First-person timetable/schedule reads. Decided without an LLM so a
# classifier miss can never send "what is my time table?" to public RAG.
_OWN_SCHEDULE_PAT = re.compile(
    r"\bmy\s+(?:time\s*table|(?:class\s+|teaching\s+)?schedule|classes|next\s+class)\b"
    r"|\bwhat\s+classes\s+do\s+i\s+have\b"
    r"|\bdo\s+i\s+have\s+(?:any\s+)?(?:class(?:es)?|labs?|lectures?|tutorials?)\b"
    r"|\b(?:what'?s|what\s+is|when\s+is|when'?s)\s+(?:my\s+)?next\s+class\b"
    r"|\b(?:my\s+)?(?:time\s*table|schedule|classes)\s+(?:for\s+)?tomorrow\b"
    r"|\btomorrow'?s\s+(?:time\s*table|schedule|classes)\b",
    re.IGNORECASE,
)

# A class-timetable request that names a cohort (year/sem + section/branch).
# Exam and event schedules are documents, not the master class timetable.
_TIMETABLE_WORD_PAT = re.compile(r"\b(?:time\s*table|schedule)\b", re.IGNORECASE)
_NON_CLASS_SCHEDULE_PAT = re.compile(
    r"\b(?:exam(?:ination)?s?|mid[\s-]?sem|end[\s-]?sem|quiz|events?|fest|convocation|"
    r"admissions?|holidays?|academic\s+calendar)\b",
    re.IGNORECASE,
)
_SECTION_PAT = re.compile(r"\b(?:sec(?:tion)?\.?\s*[a-d])\b", re.IGNORECASE)


def is_own_timetable_query(query: str) -> bool:
    return bool(
        _OWN_SCHEDULE_PAT.search(query)
        and not PUBLIC_PROGRAMME_OVERRIDE_PAT.search(query)
    )


def is_cohort_timetable_query(query: str) -> bool:
    return bool(
        _TIMETABLE_WORD_PAT.search(query)
        and not _NON_CLASS_SCHEDULE_PAT.search(query)
        and (PUBLIC_PROGRAMME_OVERRIDE_PAT.search(query) or _SECTION_PAT.search(query))
    )


def _connect_action_required(tool_results: list[dict]) -> dict | None:
    """Structured "Connect Google Calendar" CTA when a calendar tool (or the
    nested calendar_sync of a timetable edit) reports the student hasn't linked
    Google Calendar. None when no connect action is needed."""
    for r in tool_results:
        if not isinstance(r, dict):
            continue
        if r.get("status") == "calendar_not_connected":
            return {
                "type": "connect_required",
                "provider": "google_calendar",
                "connect_path": "/settings/calendar",
                "reason": "sync_timetable",
                "message": _CONNECT_THEN_SYNC_MESSAGE,
            }
    return None


def _confirmation_action_required(tool_results: list[dict]) -> dict | None:
    """Structured Confirm button for a calendar preview awaiting the student's
    go-ahead. The click travels back as a normal "confirm" chat message, so the
    confirmation regex gate stays the single write authorizer."""
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
    """Deterministic user-facing phrasing for a calendar tool result.

    The deterministic calendar path does not route results back through the
    model, so a preview always ends with the "Google Calendar ... proceed"
    phrasing the confirmation gate keys on."""
    message = result.get("message")
    status = result.get("status")

    if status == "calendar_not_connected":
        return _CONNECT_THEN_SYNC_MESSAGE
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
        return _CONNECT_THEN_SYNC_MESSAGE
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


_CALENDAR_STATUS_RE = re.compile(
    r"\b(?:calendar\s+status|(?:calendar|it)\s+(?:is\s+)?(?:connected|linked)|"
    r"(?:is|has)\s+(?:my\s+)?(?:google\s+)?calendar\s+(?:connected|linked))\b",
    re.IGNORECASE,
)
_CALENDAR_SYNC_RE = re.compile(
    r"\b(?:add|sync|put|export|save|push|import|transfer|mirror|update)\b"
    r".{0,50}\b(?:calendar|schedule|time\s*table|classes?)\b"
    r"|\b(?:schedule|time\s*table|classes?)\b.{0,40}\b(?:google\s+)?calendar\b"
    r"|\b(?:google\s+)?calendar\b.{0,40}\b(?:sync|export|import|update)\b"
    r"|\bsync\b.{0,40}\b(?:google\s+)?calendar\b.{0,40}\b(?:time\s*table|schedule|classes?)\b"
    r"|\b(?:time\s*table|schedule|classes?)\b.{0,40}\bsync\b.{0,40}\b(?:google\s+)?calendar\b",
    re.IGNORECASE,
)
# Follow-ups after an assistant turn that offered or performed a sync ("it's
# not synced", "sync it again"). Only meaningful in context: gated on the
# previous assistant turn matching _CALENDAR_SYNC_CONTEXT_RE.
_CALENDAR_SYNC_FOLLOWUP_RE = re.compile(
    r"^\s*(?:please\s+)?(?:"
    r"(?:it|it'?s|its|that|this|(?:my\s+)?(?:google\s+)?calendar|"
    r"my\s+(?:time\s*table|schedule|classes))?\s*"
    r"(?:is|was|has|have)?\s*(?:still\s+)?"
    r"(?:not|isn'?t|hasn'?t|didn'?t|wasn'?t|won'?t|never)\s*"
    r"(?:been\s+|got(?:ten)?\s+)?(?:sync(?:ed|ing)?|updated)"
    r"|(?:re-?)?sync(?:\s+(?:it|that|this|them|my\s+(?:google\s+)?calendar|"
    r"my\s+(?:time\s*table|schedule|classes)))?(?:\s+again)?"
    r")\s*[.!?]*\s*$",
    re.IGNORECASE,
)
_CALENDAR_SYNC_CONTEXT_RE = re.compile(
    r"\bsync(?:ed|ing)?\b[\s\S]{0,200}\b(?:google\s+)?calendar\b"
    r"|\bcalendar\b[\s\S]{0,200}\bsync(?:ed|ing)?\b"
    r"|\bconnect\b[\s\S]{0,80}\b(?:google\s+)?calendar\b[\s\S]{0,120}\btime\s*table\b",
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
_CONFIRMATION_RE = re.compile(
    r"^\s*(?:yes|yep|yeah|yup|sure|ok(?:ay)?|confirm(?:ed)?|proceed|"
    r"go\s+ahead|go\s+for\s+it|do\s+it(?:\s+for\s+me)?|do\s+that|"
    r"please(?:\s+do(?:\s+it(?:\s+for\s+me)?)?)?|please\s+proceed|sync\s+it)"
    r"[\s.!]*$",
    re.IGNORECASE,
)
_CALENDAR_CONFIRMATION_CONTEXT_RE = re.compile(
    r"\bgoogle calendar\b.*\b(?:confirm|proceed)\b"
    r"|\b(?:confirm|proceed)\b.*\bgoogle calendar\b"
    r"|\bconnect\b[\s\S]{0,80}\b(?:google\s+)?calendar\b"
    r"|\b(?:google\s+)?calendar\b[\s\S]{0,80}\bconnect\b",
    re.IGNORECASE | re.DOTALL,
)
# Checked before sync: "timetable ... calendar" also matches a removal request.
_CALENDAR_UNSYNC_RE = re.compile(
    r"\b(?:unsync|remove|delete|clear|wipe)\b.{0,40}"
    r"\b(?:calendar|timetable|classes?|schedule|events?)\b"
    r"|\b(?:calendar|timetable|classes?|schedule)\b.{0,30}"
    r"\b(?:unsync|remove|delete|clear|wipe)\b",
    re.IGNORECASE,
)
# The unsync prompt also contains "...Google Calendar... proceed", so this is
# checked first and keys on the removal verb the sync preview never contains.
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


def _previous_assistant(history: list[dict]) -> str:
    return next(
        (
            str(turn.get("content", ""))
            for turn in reversed(history)
            if turn.get("role") == "assistant"
        ),
        "",
    )


def _is_timetable_edit_intent(query: str) -> bool:
    """Changes to AURA's personal timetable, not calendar export."""
    return bool(_TIMETABLE_EDIT_RE.search(query))


def _is_timetable_edit_confirmation(query: str, history: list[dict]) -> bool:
    if not _CONFIRMATION_RE.fullmatch(query):
        return False
    previous = _previous_assistant(history)
    return bool(
        _TIMETABLE_EDIT_CONFIRMATION_CONTEXT_RE.search(previous)
        and not _CALENDAR_CONFIRMATION_CONTEXT_RE.search(previous)
    )


def _is_calendar_unsync_intent(query: str) -> bool:
    """A request to remove AURA's timetable events from the calendar. Never
    dispatched directly: the graph asks for confirmation first."""
    if _is_timetable_edit_intent(query) and not re.search(
        r"\b(?:from|off)\b.{0,30}\b(?:google\s+)?calendar\b",
        query,
        re.IGNORECASE,
    ):
        return False
    return bool(_CALENDAR_UNSYNC_RE.search(query))


def _required_calendar_tool(query: str, history: list[dict]) -> str | None:
    """Pin supported calendar intents to their MCP tool.

    An explicit sync request is itself authorization to update the signed-in
    student's calendar; destructive unsync requests still need a separate
    confirmation turn."""
    previous = _previous_assistant(history)
    if _CONFIRMATION_RE.fullmatch(query):
        if _CALENDAR_UNSYNC_CONFIRMATION_CONTEXT_RE.search(previous):
            return "unsync_timetable_from_calendar"
        if _CALENDAR_CONFIRMATION_CONTEXT_RE.search(previous):
            return "sync_timetable_to_calendar"

    if _CALENDAR_STATUS_RE.search(query):
        return "calendar_status"

    if (
        _TIMETABLE_DETAILS_FETCH_RE.fullmatch(query)
        and _TIMETABLE_SYNC_DETAILS_CONTEXT_RE.search(previous)
    ):
        return "sync_timetable_to_calendar"

    # Timetable edits use update_my_timetable even though they share verbs
    # ("add", "remove") with calendar requests.
    if _is_timetable_edit_intent(query):
        return None
    # A first-time removal request returns no tool: the graph asks for
    # confirmation, and the "yes" hits the confirmation arm above.
    if _CALENDAR_UNSYNC_RE.search(query):
        return None
    if _CALENDAR_SYNC_RE.search(query):
        return "sync_timetable_to_calendar"
    # Sync is idempotent, so re-running it on a "not synced" report is safe.
    if (
        _CALENDAR_SYNC_FOLLOWUP_RE.fullmatch(query)
        and _CALENDAR_SYNC_CONTEXT_RE.search(previous)
    ):
        return "sync_timetable_to_calendar"
    return None


class TimetableAgent:
    def __init__(self):
        load_dotenv()
        self.model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-32B-AWQ")

    def _call_llm(
        self,
        messages: list,
        tools: Optional[list] = None,
        tool_choice: Optional[str | dict] = None,
    ) -> Any:
        model = self.model

        def _fn(client):
            kwargs: dict = {
                "model": model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": _AGENT_MAX_TOKENS,
                "extra_body": InferenceRouter.no_think_extra_body(),
            }
            if tools:
                kwargs["tools"] = tools
            if tool_choice:
                kwargs["tool_choice"] = tool_choice
            return client.chat.completions.create(**kwargs)

        return InferenceRouter.call_with_rotation(_fn, max_retries=3)

    @staticmethod
    def _selected_tools(role: str, tool_scope: str) -> list:
        if tool_scope == SCOPE_PUBLIC_TIMETABLE:
            return [
                t for t in timetable_tools_for_role(role)
                if t.name in TIMETABLE_PUBLIC_TOOL_NAMES
            ]
        return timetable_tools_for_role(role) + calendar_mcp_tools_for_role(role)

    def _tool_schemas(self, role: str, tool_scope: str = SCOPE_PERSONAL) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._selected_tools(role, tool_scope)
        ]

    def run(
        self,
        query: str,
        identity: dict,
        history: Optional[list] = None,
        request_context=None,
        tool_scope: str = SCOPE_PERSONAL,
    ) -> dict:
        history = (history or [])[-6:]
        system = (
            PUBLIC_TIMETABLE_SYSTEM_PROMPT
            if tool_scope == SCOPE_PUBLIC_TIMETABLE
            else PERSONAL_SYSTEM_PROMPT
        )
        messages = (
            [{"role": "system", "content": system}]
            + [
                {"role": h.get("role", "user"), "content": h.get("content", "")}
                for h in history
            ]
            + [{"role": "user", "content": query}]
        )

        tool_schemas = self._tool_schemas(identity["role"], tool_scope=tool_scope)
        if not tool_schemas:
            return {"answer": "", "sources": [], "used_tools": False}

        if tool_scope != SCOPE_PUBLIC_TIMETABLE:
            # Calendar tools take no model-chosen arguments, so a decided
            # calendar intent runs without asking the model to emit a call.
            required_tool = _required_calendar_tool(query, history)
            if required_tool:
                return self._run_calendar_tool(required_tool, identity)

        response = self._call_llm(
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto",
        )
        msg = response.choices[0].message

        if not msg.tool_calls:
            # Prose without a tool call is not grounded in any data.
            return {"answer": msg.content or "", "sources": [], "used_tools": False}

        allowed_names = {t.name for t in self._selected_tools(identity["role"], tool_scope)}
        tool_messages = []
        tool_results: list[dict] = []
        for call in msg.tool_calls:
            name = call.function.name
            tool = TIMETABLE_TOOL_REGISTRY.get(name) or calendar_mcp_registry().get(name)
            if name not in allowed_names or tool is None or identity["role"] not in tool.allowed_roles:
                result = {"error": "Tool not available for this request."}
            else:
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                if name in ("update_my_timetable", "save_my_elective_selections", "set_my_cohort"):
                    # The model never authorizes a write; only a confirmation
                    # turn from the user does.
                    args.pop("confirm", None)
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
                    logger.exception("Timetable tool %s raised", name)
                    result = {"error": str(e)}

            tool_results.append(result if isinstance(result, dict) else {})
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, default=str),
            })

        succeeded = any(
            isinstance(r, dict) and r and "error" not in r for r in tool_results
        )

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
            "answer": follow_up.choices[0].message.content or "",
            "sources": [],
            "used_tools": True,
            "tool_succeeded": succeeded,
        }
        action_required = _connect_action_required(
            tool_results
        ) or _confirmation_action_required(tool_results)
        if action_required:
            out["action_required"] = action_required
        if any(
            call.function.name in TIMETABLE_MUTATING_TOOL_NAMES
            and isinstance(result, dict)
            and not result.get("error")
            and result.get("status") not in (None, "confirmation_required")
            for call, result in zip(msg.tool_calls, tool_results)
        ):
            out["timetable_changed"] = True
        return out

    def _run_calendar_tool(self, tool_name: str, identity: dict) -> dict:
        """Execute a decided calendar MCP tool directly and phrase the result.
        The tool name is fixed by the intent gate and erp_id is injected from
        the verified identity, so the model never picks whose calendar is
        touched."""
        tool = calendar_mcp_registry().get(tool_name)
        if tool is None or identity["role"] not in tool.allowed_roles:
            return {"answer": "", "sources": [], "used_tools": False}

        try:
            result = tool.handler(identity)
        except Exception as e:  # noqa: BLE001 -- surfaced as a soft calendar error
            logger.exception("Calendar MCP tool %s raised", tool_name)
            result = {"error": str(e)}
        if not isinstance(result, dict):
            result = {}
        if "error" in result:
            logger.error("Calendar MCP tool %s errored: %s", tool_name, result["error"])

        out: dict = {
            "answer": _phrase_calendar_result(tool_name, result),
            "sources": [],
            "used_tools": True,
            "tool_succeeded": "error" not in result,
        }
        action_required = _connect_action_required(
            [result]
        ) or _confirmation_action_required([result])
        if action_required:
            out["action_required"] = action_required
        return out
