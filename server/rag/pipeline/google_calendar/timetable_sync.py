"""
timetable_sync.py — glue between a student's AURA timetable and their
Google Calendar. Shared by:
  - api/routes/calendar_routes.py  (POST/DELETE /calendar/timetable/sync — the
    manual Settings > Calendar flow)
  - mcp_servers/gcal_server.py (the Google Calendar MCP server, reached by the
    agent orchestrator via pipeline/timetable/calendar_mcp_client.py, so a
    student can trigger this conversationally)

All logic for "is this student allowed / what happens if not connected"
lives here. Callers just call preview() / apply() / unsync().
"""

from __future__ import annotations

from .token_vault import is_linked, has_write_scope, CalendarNotLinked
from ..timetable import service as timetable_service
from ..timetable.service import DAY_NAMES as _DAY_NAMES


def _dow_name(slot: dict) -> str:
    """Converts day_of_week int (0=Mon) to a readable name for preview output."""
    dow = slot.get("day_of_week")
    if dow is None:
        return slot.get("day", "?")
    try:
        return _DAY_NAMES[int(dow)]
    except (IndexError, TypeError, ValueError):
        return str(dow)


def _erp_id(identity) -> str:
    return timetable_service.field(identity, "erp_id")


def status(identity) -> dict:
    erp_id = _erp_id(identity)
    linked = is_linked(erp_id) and has_write_scope(erp_id)
    return {"calendar_linked": linked}


def preview(identity, scope: str = "full", subject_code: str | None = None) -> dict:
    """
    Preview what a sync would do — returns slot list without writing anything.
    Used for the confirm-before-write step in the agent tool.
    """
    erp_id = _erp_id(identity)
    if not is_linked(erp_id) or not has_write_scope(erp_id):
        return {
            "status": "calendar_not_connected",
            "message": (
                "Your Google Calendar isn't connected for writing yet. "
                "Connect it from Settings first, then ask me to sync again."
            ),
        }
    try:
        effective = timetable_service.get_effective_timetable(identity)
    except timetable_service.TimetableError as e:
        return {"status": "error", "message": str(e)}

    from .writer import _filter_slots
    slots = _filter_slots(effective["timetable"], scope, subject_code)

    return {
        "status": "confirmation_required",
        "class_count": len(slots),
        "scope": scope,
        "preview": [
            {
                "day":          _dow_name(s),
                "start":        s["start_time"],
                "course_code":  s["course_code"],
                "session_type": s.get("session_type", "lecture"),
            }
            for s in slots
        ],
        "message": (
            f"This will create or update {len(slots)} recurring weekly events on your "
            "Google Calendar — one per class — with popup reminders, running until the "
            "end of the semester. Confirm to proceed."
        ),
    }


def apply(
    identity,
    *,
    scope: str = "full",
    subject_code: str | None = None,
    async_mode: bool = True,
) -> dict:
    """
    Perform the sync. In async_mode (default), enqueues a background job and
    returns immediately with {status: queued, job_id}. In sync_mode (for the
    agent tool which needs the result inline), blocks until done.
    """
    erp_id = _erp_id(identity)
    if not is_linked(erp_id) or not has_write_scope(erp_id):
        return {
            "status": "calendar_not_connected",
            "message": "Google Calendar is not connected for writing.",
        }
    try:
        effective = timetable_service.get_effective_timetable(identity)
    except timetable_service.TimetableError as e:
        return {"status": "error", "message": str(e)}

    slots = effective["timetable"]

    if async_mode:
        from .sync_job import enqueue_sync
        try:
            job_id = enqueue_sync(erp_id, slots, scope=scope, subject_code=subject_code)
        except ValueError as e:
            return {"status": "already_running", "message": str(e)}
        return {
            "status": "queued",
            "job_id": job_id,
            "message": (
                f"Sync started in the background for {len(slots)} slots. "
                "Check status at GET /calendar/timetable/sync/status."
            ),
        }
    else:
        # Synchronous path (agent tool)
        from .writer import sync_timetable, CalendarWriteError
        try:
            result = sync_timetable(erp_id, slots, scope=scope, subject_code=subject_code)
        except CalendarWriteError as e:
            return {"status": "error", "message": str(e)}
        except CalendarNotLinked:
            return {"status": "calendar_not_connected", "message": "Google Calendar is not connected."}
        return {"status": "synced", **result}


def unsync(identity, *, keep_events: bool = False) -> dict:
    erp_id = _erp_id(identity)
    if not is_linked(erp_id):
        return {"status": "calendar_not_connected"}
    from .writer import unsync_all
    removed = unsync_all(erp_id, keep_events=keep_events)
    return {
        "status":       "unsynced",
        "removed":      removed,
        "events_kept":  keep_events,
    }


def resync_if_linked(identity) -> dict:
    """Best-effort Google Calendar refresh, called right after any
    timetable-changing action -- whether that action came from the
    dashboard's edit form or the chat agent's update_my_timetable /
    undo_timetable_change tools. Both callers funnel through here so there
    is exactly one place deciding "is this student's calendar linked with
    write access, and should we push the new timetable to it" -- same
    reasoning as preview()/apply() above.

    Deliberately does NOT prompt for a fresh confirm/OAuth step: if the
    student hasn't already granted calendar write access, this is a no-op
    rather than an error, since a small timetable edit shouldn't force a
    Google consent screen on someone who never asked to sync in the first
    place. And a failure here must never bubble up as a failure of the
    edit itself -- the timetable change already succeeded by the time this
    runs, so at worst the calendar is left stale until the next sync.
    """
    erp_id = _erp_id(identity)
    if not erp_id or not is_linked(erp_id) or not has_write_scope(erp_id):
        return {"status": "not_connected"}
    try:
        return apply(identity, async_mode=False)
    except Exception as e:  # noqa: BLE001 -- deliberately broad, see docstring
        return {"status": "error", "message": str(e)}
