"""
tool_registry.py — timetable tools exposed to the agent orchestrator.

Kept as a separate registry from pipeline.ecampus.tool_registry (which is
read-only against the ERP) because update_my_timetable is a genuine, and
deliberate, write tool: it lets a student change their own AURA-side
timetable view. It is merged into the same orchestrator tool-calling loop
in pipeline.ecampus.orchestrator — see MERGED_TOOL_REGISTRIES there.

Every handler receives `identity` from the verified internal JWT and NEVER
accepts a student_id/erp_id argument from the model — a student can only
ever read or edit their own timetable, by construction.
"""

from dataclasses import dataclass
from typing import Callable

from . import service


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    category: str             # "read" | "derived" | "write"
    allowed_roles: list[str]
    handler: Callable


def _handle_get_my_timetable(identity, **kwargs):
    try:
        return service.get_effective_timetable(identity)
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_list_my_timetable_changes(identity, **kwargs):
    try:
        return {"changes": service.list_my_changes(identity)}
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_update_my_timetable(identity, **kwargs):
    """`confirm` gates the actual write. On the first call (confirm missing
    or false) this returns a preview of the change instead of applying it,
    per SYSTEM_PROMPT's confirm-before-write instruction — the LLM is
    expected to show the user the preview and only call again with
    confirm=true once the user explicitly agrees."""
    confirm = bool(kwargs.pop("confirm", False))
    try:
        if not confirm:
            year = sem = sec = None
            if service.field(identity, "role") == "student":
                year = service.field(identity, "current_year")
                sem = service.field(identity, "current_sem")
                sec = service.field(identity, "current_sec")
            return {
                "status": "confirmation_required",
                "preview": {k: v for k, v in kwargs.items() if v is not None},
                "message": (
                    "Here is the change I'm about to make to your timetable — confirm and "
                    "I'll apply it, or tell me what to adjust."
                ),
                "cohort": {"year": year, "sem": sem, "sec": sec},
            }
        result = service.apply_change(identity, **kwargs)
        return {"status": "applied", **result}
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_undo_timetable_change(identity, **kwargs):
    try:
        override_id = kwargs.get("override_id")
        if not override_id:
            return {"error": "override_id is required — use list_my_timetable_changes to find it."}
        return {"status": "applied", **service.clear_change(identity, override_id)}
    except service.TimetableError as e:
        return {"error": str(e)}


GET_MY_TIMETABLE = Tool(
    name="get_my_timetable",
    description=(
        "Get the requester's own current weekly class timetable (lectures, labs, tutorials), "
        "already merged with any personal changes they've previously asked AURA to make."
    ),
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_my_timetable,
)

LIST_MY_TIMETABLE_CHANGES = Tool(
    name="list_my_timetable_changes",
    description="List the personal changes the requester has previously made to their own timetable.",
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_list_my_timetable_changes,
)

UPDATE_MY_TIMETABLE = Tool(
    name="update_my_timetable",
    description=(
        "Change, add, or remove ONE entry on the requester's own timetable — for example moving "
        "a class to a different room/time, or adding a new lab session. This ONLY ever affects "
        "the requester's own view; nobody else's timetable is touched. Always call this once "
        "with confirm=false first to preview the change, then relay the preview to the user and "
        "only call it again with confirm=true after they explicitly agree."
    ),
    parameters={
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["replace", "add", "remove"],
                "description": (
                    "'replace' to change an existing class's time/room/etc, 'add' for a brand-new "
                    "class that isn't on the master timetable, 'remove' to hide an existing class."
                ),
            },
            "day": {"type": "string", "description": "Weekday name, e.g. 'Tuesday'."},
            "start_time": {"type": "string", "description": "HH:MM 24-hour, e.g. '17:00'."},
            "end_time": {"type": "string", "description": "HH:MM 24-hour, e.g. '18:30'."},
            "course_code": {"type": "string", "description": "Existing course code to match, for replace/remove."},
            "course_name": {"type": "string"},
            "session_type": {"type": "string", "enum": ["lecture", "lab", "tutorial"]},
            "room": {"type": "string"},
            "faculty_name": {"type": "string"},
            "note": {"type": "string", "description": "Short note on why, for the student's own record."},
            "confirm": {"type": "boolean", "description": "Set true only after the user has confirmed the previewed change."},
        },
        "required": ["kind"],
    },
    category="write", allowed_roles=["student"], handler=_handle_update_my_timetable,
)

UNDO_TIMETABLE_CHANGE = Tool(
    name="undo_timetable_change",
    description="Revert one previous personal timetable change back to the original master schedule.",
    parameters={
        "type": "object",
        "properties": {"override_id": {"type": "string", "description": "id from list_my_timetable_changes"}},
        "required": ["override_id"],
    },
    category="write", allowed_roles=["student"], handler=_handle_undo_timetable_change,
)


TOOL_REGISTRY: dict[str, Tool] = {
    t.name: t for t in [
        GET_MY_TIMETABLE, LIST_MY_TIMETABLE_CHANGES, UPDATE_MY_TIMETABLE, UNDO_TIMETABLE_CHANGE,
    ]
}


def tools_for_role(role: str) -> list[Tool]:
    return [t for t in TOOL_REGISTRY.values() if role in t.allowed_roles]
