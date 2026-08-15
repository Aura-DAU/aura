# Meetings service — returns a calendar OWNER's own events with full
# detail (title, start, end). Distinct from slot_service.py, which derives
# free/busy windows for someone ELSE's calendar (a student checking when a
# faculty member is free) and deliberately never exposes event titles.
# This module is only ever called with the requester's own erp_id (see
# api/routes/calendar_routes.py::get_my_meetings), so showing the real
# summary is fine — it's the same detail they'd see opening Google
# Calendar themselves.

import datetime

from .client import get_events_on_date
from .token_vault import CalendarNotLinked, is_linked


def get_my_meetings(erp_id: str, date: datetime.date) -> dict:
    """Returns this user's own Google Calendar events for a date, for
    display alongside their AURA class timetable (see
    pipeline.timetable.service.get_faculty_timetable / get_effective_timetable
    and aura/components/ui/faculty-dashboard.tsx, which merge the two).
    Never raises: an unlinked or expired calendar simply comes back with
    calendar_linked=False rather than an error, matching slot_service.py's
    convention."""
    if not is_linked(erp_id):
        return {
            "erp_id": erp_id,
            "date": date.isoformat(),
            "calendar_linked": False,
            "meetings": [],
            "note": "Google Calendar isn't connected to AURA yet.",
        }

    try:
        events = get_events_on_date(erp_id, date)
    except CalendarNotLinked:
        return {
            "erp_id": erp_id,
            "date": date.isoformat(),
            "calendar_linked": False,
            "meetings": [],
            "note": "Calendar token expired. Please reconnect your calendar.",
        }
    except Exception as e:
        return {
            "erp_id": erp_id,
            "date": date.isoformat(),
            "calendar_linked": True,
            "meetings": [],
            "note": f"Could not fetch calendar: {e}",
        }

    # Skip transparent ("free") events like all-day availability blocks —
    # only real meetings/appointments belong in a schedule view.
    meetings = [ev for ev in events if ev.get("is_busy")]

    return {
        "erp_id": erp_id,
        "date": date.isoformat(),
        "calendar_linked": True,
        "meetings": meetings,
    }
