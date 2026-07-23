"""
timetable_sync.py — glue between a student's AURA timetable and their
Google Calendar. Shared by:
  - api/routes/calendar_routes.py  (POST/DELETE /calendar/timetable/sync)
  - pipeline/timetable/tool_registry.py (sync_timetable_to_google_calendar
    agent tool, so a student can trigger this conversationally)

Kept out of both callers so there's exactly one place that decides "is this
student allowed to have events written, and what happens if the calendar
isn't linked yet" — the FastAPI route and the tool handler each just call
`preview()` / `apply()` below and format the result for their own surface.
"""

from __future__ import annotations

from . import writer
from .token_vault import is_linked, has_write_scope, CalendarNotLinked
from ..timetable import service as timetable_service


def _erp_id(identity) -> str:
    return timetable_service.field(identity, "erp_id")


def status(identity) -> dict:
    erp_id = _erp_id(identity)
    linked = is_linked(erp_id) and has_write_scope(erp_id)
    return {"calendar_linked": linked}


def preview(identity) -> dict:
    """What a sync would do, without writing anything — used for the
    confirm-before-write step in the agent tool."""
    erp_id = _erp_id(identity)
    if not is_linked(erp_id) or not has_write_scope(erp_id):
        return {
            "status": "calendar_not_connected",
            "message": (
                "Your Google Calendar isn't connected for writing yet. "
                "Connect it from Settings first (this asks Google for "
                "permission to create events on your calendar), then ask "
                "me to sync again."
            ),
        }
    try:
        effective = timetable_service.get_effective_timetable(identity)
    except timetable_service.TimetableError as e:
        return {"status": "error", "message": str(e)}

    slots = effective["timetable"]
    return {
        "status": "confirmation_required",
        "class_count": len(slots),
        "preview": [
            {"day": s["day"], "start": s["start_time"], "course_code": s["course_code"]}
            for s in slots
        ],
        "message": (
            f"This will create or update {len(slots)} recurring weekly events on your "
            "Google Calendar — one per class — with popup reminders, running until the "
            "end of the semester. Confirm to proceed."
        ),
    }


def apply(identity) -> dict:
    """Actually performs the sync. Caller (route or tool handler) is
    responsible for having already gotten explicit user confirmation."""
    erp_id = _erp_id(identity)
    if not is_linked(erp_id) or not has_write_scope(erp_id):
        return {"status": "calendar_not_connected", "message": "Google Calendar is not connected for writing."}
    try:
        effective = timetable_service.get_effective_timetable(identity)
    except timetable_service.TimetableError as e:
        return {"status": "error", "message": str(e)}

    try:
        result = writer.sync_timetable(erp_id, effective["timetable"])
    except writer.CalendarWriteError as e:
        return {"status": "error", "message": str(e)}
    except CalendarNotLinked:
        return {"status": "calendar_not_connected", "message": "Google Calendar is not connected."}

    return {"status": "synced", **result}


def unsync(identity) -> dict:
    erp_id = _erp_id(identity)
    if not is_linked(erp_id):
        return {"status": "calendar_not_connected"}
    removed = writer.unsync_all(erp_id)
    return {"status": "unsynced", "removed": removed}
