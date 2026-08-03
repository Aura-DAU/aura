"""
tool_registry.py -- timetable tools exposed to the agent orchestrator.

Kept as a separate registry from pipeline.ecampus.tool_registry (which is
read-only against the ERP) because update_my_timetable is a genuine, and
deliberate, write tool: it lets a student change their own AURA-side
timetable view. It is merged into the same orchestrator tool-calling loop
in pipeline.ecampus.orchestrator -- see MERGED_TOOL_REGISTRIES there.

Every handler receives `identity` from the verified internal JWT and NEVER
accepts a student_id/erp_id argument from the model -- a student can only
ever read or edit their own timetable, by construction.

Faculty get a read-only view of their teaching schedule.
"""

from dataclasses import dataclass
from typing import Callable

from . import service
from ..google_calendar import timetable_sync


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    category: str             # "read" | "derived" | "write"
    allowed_roles: list[str]
    handler: Callable


# -- Student read tools -------------------------------------------------------

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


# -- Student write tools -------------------------------------------------------

def _handle_update_my_timetable(identity, **kwargs):
    """`confirm` gates the actual write. On the first call (confirm missing
    or false) this returns a preview of the change instead of applying it,
    per SYSTEM_PROMPT's confirm-before-write instruction -- the LLM is
    expected to show the user the preview and only call again with
    confirm=true once the user explicitly agrees."""
    confirm = bool(kwargs.pop("confirm", False))
    kwargs.pop("request_context", None)
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
                    "Here is the change I'm about to make to your timetable -- confirm and "
                    "I'll apply it, or tell me what to adjust."
                ),
                "cohort": {"year": year, "sem": sem, "sec": sec},
            }
        result = service.apply_change(identity, **kwargs)
        result["calendar_sync"] = timetable_sync.resync_if_linked(identity)
        return {"status": "applied", **result}
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_undo_timetable_change(identity, **kwargs):
    try:
        override_id = kwargs.get("override_id")
        if not override_id:
            return {"error": "override_id is required -- use list_my_timetable_changes to find it."}
        result = service.clear_change(identity, override_id)
        result["calendar_sync"] = timetable_sync.resync_if_linked(identity)
        return {"status": "applied", **result}
    except service.TimetableError as e:
        return {"error": str(e)}


# -- Any-cohort read tool (not scoped to the requester's own cohort) ----------

def _handle_get_cohort_timetable(identity, **kwargs):
    try:
        return service.get_timetable_for_cohort(
            year=kwargs.get("year"),
            sem=kwargs.get("sem"),
            sec=kwargs.get("sec"),
            branch=kwargs.get("branch"),
            program=kwargs.get("program"),
        )
    except service.TimetableError as e:
        return {"error": str(e)}


# -- Faculty read tools --------------------------------------------------------

def _handle_get_faculty_timetable(identity, **kwargs):
    """Returns all classes taught by the requesting faculty member,
    across every batch/section/year."""
    try:
        return service.get_faculty_timetable(identity)
    except service.TimetableError as e:
        return {"error": str(e)}


# -- Elective selection tools --------------------------------------------------

def _handle_get_available_electives(identity, **kwargs):
    try:
        return service.get_available_electives(identity)
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_save_my_elective_selections(identity, **kwargs):
    """Confirm-gated: first call returns a preview of what will be saved,
    second call with confirm=true actually saves."""
    confirm = bool(kwargs.pop("confirm", False))
    course_codes = kwargs.get("course_codes", [])
    if not course_codes:
        return {"error": "Please provide a list of course_codes for the electives you are taking."}
    try:
        if not confirm:
            return {
                "status": "confirmation_required",
                "preview": {"course_codes": course_codes},
                "message": (
                    "I will save these as your elective selections. Your timetable will then "
                    "show only these electives (plus all your core courses). Confirm to proceed."
                ),
            }
        return service.save_elective_selections(identity, course_codes)
    except service.TimetableError as e:
        return {"error": str(e)}


def _handle_set_my_cohort(identity, **kwargs):
    confirm = bool(kwargs.pop("confirm", False))
    year = kwargs.get("year")
    sem = kwargs.get("sem")
    sec = kwargs.get("sec")
    try:
        if not confirm:
            return {
                "status": "confirmation_required",
                "preview": {"year": year, "sem": sem, "sec": sec},
                "message": (
                    f"I will update your profile section/cohort to Year {year or 'current'}, "
                    f"Semester {sem or 'current'}, Section {sec or 'current'}. Confirm to save."
                ),
            }
        return service.update_student_cohort(identity, year=year, sem=sem, sec=sec)
    except service.TimetableError as e:
        return {"error": str(e)}


# -- Tool definitions ----------------------------------------------------------

SET_MY_COHORT = Tool(
    name="set_my_cohort",
    description=(
        "Update the student's cohort section, semester, or academic year (e.g. changing from Section A to Section B). "
        "This saves the student's section into PostgreSQL user_identity_map for all future sessions. "
        "Always call with confirm=false first to preview, then confirm=true after user agrees."
    ),
    parameters={
        "type": "object",
        "properties": {
            "sec": {"type": "string", "description": "Section letter, e.g. 'A', 'B', 'C', 'D'."},
            "sem": {"type": "integer", "description": "Semester number, e.g. 1, 3, 5, 7."},
            "year": {"type": "integer", "description": "Academic year number, e.g. 1, 2, 3, 4."},
            "confirm": {"type": "boolean", "description": "Set true after user confirms."},
        },
    },
    category="write", allowed_roles=["student"], handler=_handle_set_my_cohort,
)

GET_MY_TIMETABLE = Tool(
    name="get_my_timetable",
    description=(
        "Get the requester's own current weekly class timetable (lectures, labs, tutorials), "
        "already merged with any personal changes they've previously asked AURA to make."
    ),
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_my_timetable,
)

GET_COHORT_TIMETABLE = Tool(
    name="get_cohort_timetable",
    description=(
        "Look up the published weekly class timetable for ANY cohort by semester/year, "
        "section, and branch/programme -- e.g. 'give me the timetable of BTech ICT 3rd sem "
        "section A' or 'what's the schedule for 2nd year MnC section B'. Returns the plain "
        "master schedule only (no personal overrides or elective picks applied). Use "
        "get_my_timetable instead when the requester is asking about their OWN timetable. "
        "Section defaults to 'A' if the user doesn't name one."
    ),
    parameters={
        "type": "object",
        "properties": {
            "sem": {
                "type": "integer",
                "description": "Semester number, e.g. 1, 3, 5, 7. Prefer this when the user names a semester.",
            },
            "year": {
                "type": "integer",
                "description": "Academic year 1-4, if the user says 'year' instead of 'semester'.",
            },
            "sec": {
                "type": "string",
                "description": "Section letter, e.g. 'A', 'B', 'C', 'D'. Defaults to 'A' if not given.",
            },
            "branch": {
                "type": "string",
                "description": "Branch, e.g. 'ICT', 'ICT-CS', 'MnC', 'EVD'.",
            },
            "program": {
                "type": "string",
                "description": "Degree programme, e.g. 'BTech', 'MTech', 'MSc'.",
            },
        },
    },
    category="read", allowed_roles=["student", "faculty"], handler=_handle_get_cohort_timetable,
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
        "Change, add, or remove ONE entry on the requester's own timetable -- for example moving "
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
                    "class that isn't on the master timetable, 'remove' to hide an existing class. "
                    "If the student already connected Google Calendar with write access, a confirmed "
                    "change also refreshes their synced calendar automatically -- no separate sync call needed."
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

GET_FACULTY_TIMETABLE = Tool(
    name="get_my_teaching_schedule",
    description=(
        "Get the requesting faculty member's full weekly teaching schedule, showing every "
        "class they teach across all batches, sections, and years."
    ),
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["faculty"], handler=_handle_get_faculty_timetable,
)


GET_AVAILABLE_ELECTIVES = Tool(
    name="get_available_electives",
    description=(
        "Get the list of elective courses available for the student's cohort this semester, "
        "along with which ones the student has already selected. Use this when the student "
        "asks about electives, wants to see which electives they picked, or needs to change "
        "their elective selections."
    ),
    parameters={"type": "object", "properties": {}},
    category="read", allowed_roles=["student"], handler=_handle_get_available_electives,
)

SAVE_MY_ELECTIVE_SELECTIONS = Tool(
    name="save_my_elective_selections",
    description=(
        "Save the student's chosen elective courses for this semester. After saving, the "
        "student's timetable will only show their core courses plus the selected electives "
        "(other electives they didn't pick will be hidden). The student can change their "
        "selections at any time by calling this tool again with the updated list. Always "
        "call with confirm=false first to preview, then confirm=true after student agrees."
    ),
    parameters={
        "type": "object",
        "properties": {
            "course_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "List of course codes for the electives the student is taking, "
                    "e.g. ['IT301', 'SC205']. Use get_available_electives to see valid codes."
                ),
            },
            "confirm": {
                "type": "boolean",
                "description": "Set true only after the user has confirmed the previewed selection.",
            },
        },
        "required": ["course_codes"],
    },
    category="write", allowed_roles=["student"], handler=_handle_save_my_elective_selections,
)


TOOL_REGISTRY: dict[str, Tool] = {
    t.name: t for t in [
        GET_MY_TIMETABLE, GET_COHORT_TIMETABLE, LIST_MY_TIMETABLE_CHANGES, UPDATE_MY_TIMETABLE,
        UNDO_TIMETABLE_CHANGE,
        GET_FACULTY_TIMETABLE, GET_AVAILABLE_ELECTIVES, SAVE_MY_ELECTIVE_SELECTIONS,
        SET_MY_COHORT,
    ]
}

# Exposed on the public-KB / COMMUNITY orchestrator path too (see
# pipeline.ecampus.orchestrator) -- looking up another cohort's published
# timetable isn't the requester's own private data, so a student should be
# able to ask for it even when the query doesn't classify as PERSONAL_DATA.
PUBLIC_TOOL_NAMES: frozenset[str] = frozenset({"get_cohort_timetable"})


def tools_for_role(role: str) -> list[Tool]:
    return [t for t in TOOL_REGISTRY.values() if role in t.allowed_roles]
