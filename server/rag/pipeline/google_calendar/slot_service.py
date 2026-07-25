"""
Slot service — derives available booking windows from a faculty's calendar.

Takes the raw Google Calendar events for a day and returns time windows
where the faculty member has no conflicting events — their "available slots".
Faculty publish these slots; students see only the slots for their own
enrolled courses or BTP guide.
"""

import datetime
from typing import Optional
from .client import get_events_on_date
from .token_vault import CalendarNotLinked, is_linked

# Configurable working window (IST context — adjust as needed)
WORK_START = datetime.time(9, 0)
WORK_END   = datetime.time(18, 0)
SLOT_MINS  = 30  # granularity of each slot


def _time_range_overlaps(
    s1: datetime.time, e1: datetime.time,
    s2: datetime.time, e2: datetime.time,
) -> bool:
    return s1 < e2 and s2 < e1


def _parse_time(dt_str: Optional[str]) -> Optional[datetime.time]:
    if not dt_str:
        return None
    try:
        # ISO format: 2026-07-04T10:30:00Z
        dt = datetime.datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        # Convert to IST (UTC+5:30)
        dt_ist = dt + datetime.timedelta(hours=5, minutes=30)
        return dt_ist.time().replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def get_available_slots(
    faculty_erp_id: str,
    date: datetime.date,
) -> dict:
    """
    Returns available 30-minute slot windows for a faculty member on a date.
    Used by students to see when they can book a meeting.

    Returns:
      {
        "faculty_erp_id": ...,
        "date": "2026-07-04",
        "calendar_linked": bool,
        "available_slots": [{"start": "10:00", "end": "10:30"}, ...],
        "note": "..."
      }
    """
    if not is_linked(faculty_erp_id):
        return {
            "faculty_erp_id":  faculty_erp_id,
            "date":            date.isoformat(),
            "calendar_linked": False,
            "available_slots": [],
            "note": "This faculty member has not connected their Google Calendar to AURA.",
        }

    try:
        events = get_events_on_date(faculty_erp_id, date)
    except CalendarNotLinked:
        return {
            "faculty_erp_id":  faculty_erp_id,
            "date":            date.isoformat(),
            "calendar_linked": False,
            "available_slots": [],
            "note": "Calendar token expired. Faculty needs to reconnect.",
        }
    except Exception as e:
        return {
            "faculty_erp_id":  faculty_erp_id,
            "date":            date.isoformat(),
            "calendar_linked": True,
            "available_slots": [],
            "note": f"Could not fetch calendar: {e}",
        }

    # Build list of busy windows from events where is_busy=True
    busy: list[tuple[datetime.time, datetime.time]] = []
    for ev in events:
        if not ev.get("is_busy"):
            continue
        start = _parse_time(ev.get("start"))
        end   = _parse_time(ev.get("end"))
        if start and end and start < end:
            busy.append((start, end))

    # Walk the work day in SLOT_MINS increments, exclude busy windows
    available = []
    cursor = datetime.datetime.combine(date, WORK_START)
    work_end = datetime.datetime.combine(date, WORK_END)

    while cursor + datetime.timedelta(minutes=SLOT_MINS) <= work_end:
        slot_start = cursor.time()
        slot_end   = (cursor + datetime.timedelta(minutes=SLOT_MINS)).time()
        if not any(_time_range_overlaps(slot_start, slot_end, b[0], b[1]) for b in busy):
            available.append({
                "start": slot_start.strftime("%H:%M"),
                "end":   slot_end.strftime("%H:%M"),
            })
        cursor += datetime.timedelta(minutes=SLOT_MINS)

    return {
        "faculty_erp_id":  faculty_erp_id,
        "date":            date.isoformat(),
        "calendar_linked": True,
        "available_slots": available,
        "busy_count":      len(busy),
        "note": "Slots are 30-minute windows with no calendar conflicts.",
    }