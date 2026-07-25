"""
writer.py — the ONLY module in AURA that writes events to a Google Calendar.

v8 addition. Everything else in pipeline/google_calendar/ and
pipeline/ecampus/ remains strictly read-only (enforced by the static-analysis
guard in pipeline/tests/test_write_tool_removal.py). This module is the
single, explicitly-allowlisted exception, and it only ever touches the
calendar of the erp_id that owns the `calendar.events` grant it's using —
never anyone else's.

What gets written: one recurring weekly Google Calendar event per unique
class slot on the student's *effective* AURA timetable (master schedule +
their own overrides — see pipeline/timetable/service.py), each using an
RRULE bounded by GOOGLE_CALENDAR_SEMESTER_END so it stops repeating at the
end of the semester rather than forever. Each event is tagged with an
extendedProperties.private.aura_slot_key so a re-sync updates the existing
event in place (PATCH) instead of creating a duplicate, and so unsync/
disconnect can find and delete exactly what AURA created — nothing else on
the student's calendar is ever touched.

Reminders are set directly on each event via Google's own `reminders`
field (popup notifications). This is deliberate: once the event exists,
notification delivery is entirely Google Calendar's job — its apps and
web client already handle desktop, laptop, Android, and iOS, so AURA does
not need to run its own delivery pipeline for these reminders (contrast
with pipeline/timetable/notifier.py's Web Push reminders, which are a
separate, AURA-native mechanism this feature does not replace).
"""

from __future__ import annotations

import os
import datetime
import logging

import requests

from .client import get_valid_access_token
from .token_vault import (
    get_synced_event_map,
    record_synced_event,
    forget_synced_event,
)

logger = logging.getLogger("aura.google_calendar.writer")

GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
CAL_ID = "primary"

# Minutes-before-class popup reminders, comma-separated. Defaults to two
# reminders: 30 minutes and 10 minutes before class starts.
REMINDER_MINUTES = [
    int(m) for m in os.environ.get("GOOGLE_CALENDAR_REMINDER_MINUTES", "30,10").split(",")
    if m.strip()
]

# RRULE UNTIL bound — required so events don't recur forever. Set by
# whoever administers the semester's timetable_master rows.
SEMESTER_END = os.environ.get("GOOGLE_CALENDAR_SEMESTER_END", "")

_RRULE_DAY = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]


class CalendarWriteError(Exception):
    pass


def _semester_end_date() -> datetime.date:
    if not SEMESTER_END:
        raise CalendarWriteError(
            "GOOGLE_CALENDAR_SEMESTER_END is not configured on the server — "
            "the AURA administrator needs to set this to the last day of "
            "the current semester before timetable sync can run."
        )
    try:
        return datetime.date.fromisoformat(SEMESTER_END)
    except ValueError:
        raise CalendarWriteError(f"GOOGLE_CALENDAR_SEMESTER_END is not a valid date: {SEMESTER_END!r}")


def _slot_key(slot: dict) -> str:
    """Stable key for one timetable slot, used both as the RRULE anchor
    and as the lookup key in gcal_synced_events. Uses the AURA slot id
    (master row id, or override id for personal changes) rather than
    day/time/course so a slot that gets edited (still the same id) updates
    the same Google event instead of creating a new one."""
    return str(slot["id"])


def _next_occurrence(day_of_week: int, start_time: str, end_time: str) -> tuple[datetime.datetime, datetime.datetime]:
    """First future occurrence (today counts if the class hasn't started
    yet) of a weekly slot, as the DTSTART/DTEND for the RRULE."""
    today = datetime.date.today()
    days_ahead = (day_of_week - today.weekday()) % 7
    candidate = today + datetime.timedelta(days=days_ahead)
    sh, sm = (int(x) for x in start_time.split(":")[:2])
    eh, em = (int(x) for x in end_time.split(":")[:2])
    if days_ahead == 0 and datetime.datetime.now().time() > datetime.time(sh, sm):
        candidate += datetime.timedelta(days=7)
    start = datetime.datetime.combine(candidate, datetime.time(sh, sm))
    end = datetime.datetime.combine(candidate, datetime.time(eh, em))
    return start, end


def _event_body(slot: dict, tz: str) -> dict:
    start, end = _next_occurrence(slot["day_of_week"], slot["start_time"], slot["end_time"])
    # Bug 3 fix: use a DATE-only UNTIL (no time/Z suffix) to avoid ambiguity
    # when mixing a UTC-suffixed UNTIL with timezone-aware event datetimes.
    # RFC 5545 §3.8.5.3 allows DATE form for weekly recurring events.
    until = _semester_end_date().strftime("%Y%m%d")
    rrule = f"RRULE:FREQ=WEEKLY;BYDAY={_RRULE_DAY[slot['day_of_week']]};UNTIL={until}"

    location_parts = [p for p in (slot.get("room"),) if p]
    description_lines = [f"{slot['session_type'].capitalize()} — synced from AURA."]
    if slot.get("faculty_name"):
        description_lines.append(f"Faculty: {slot['faculty_name']}")
    description_lines.append("Edit this class in AURA, then re-sync, to keep this event up to date.")

    return {
        "summary": f"{slot['course_name']} ({slot['course_code']})",
        "location": ", ".join(location_parts) or None,
        "description": "\n".join(description_lines),
        "start": {"dateTime": start.isoformat(), "timeZone": tz},
        "end": {"dateTime": end.isoformat(), "timeZone": tz},
        "recurrence": [rrule],
        "reminders": {
            "useDefault": False,
            "overrides": [{"method": "popup", "minutes": m} for m in REMINDER_MINUTES],
        },
        "extendedProperties": {"private": {"aura_slot_key": _slot_key(slot), "aura_managed": "true"}},
    }


def _make_headers(access_token: str) -> dict:
    """Build auth headers from an already-fetched access token.
    Takes the token as a parameter (Bug 6 fix) so callers fetch it once
    per operation rather than once per API call inside a loop."""
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def sync_timetable(erp_id: str, timetable_slots: list[dict], tz: str = "Asia/Kolkata") -> dict:
    """Upserts one recurring event per slot. Returns a summary the caller
    can relay back to the student: {created, updated, removed, errors}."""
    # Bug 6 fix: fetch the access token once for the whole sync, not once
    # per API call inside the loop (which could cause repeated refresh checks).
    access_token = get_valid_access_token(erp_id)
    hdrs = _make_headers(access_token)

    existing = get_synced_event_map(erp_id)
    seen_keys: set[str] = set()
    created = updated = removed = 0
    errors: list[str] = []

    for slot in timetable_slots:
        key = _slot_key(slot)
        seen_keys.add(key)
        body = _event_body(slot, tz)
        try:
            if key in existing:
                resp = requests.patch(
                    GOOGLE_EVENTS_URL.format(cal_id=CAL_ID) + f"/{existing[key]}",
                    headers=hdrs, json=body, timeout=10,
                )
                if resp.status_code == 404:
                    # Event was deleted on the Google side out-of-band — recreate it.
                    resp = requests.post(
                        GOOGLE_EVENTS_URL.format(cal_id=CAL_ID),
                        headers=hdrs, json=body, timeout=10,
                    )
                    resp.raise_for_status()
                    record_synced_event(erp_id, key, resp.json()["id"])
                    created += 1
                else:
                    resp.raise_for_status()
                    updated += 1
            else:
                resp = requests.post(
                    GOOGLE_EVENTS_URL.format(cal_id=CAL_ID),
                    headers=hdrs, json=body, timeout=10,
                )
                resp.raise_for_status()
                record_synced_event(erp_id, key, resp.json()["id"])
                created += 1
        except requests.RequestException as e:
            logger.warning("Calendar sync failed for slot %s (erp_id=%s): %s", key, erp_id, e)
            errors.append(f"{slot.get('course_code', '?')} on {slot.get('day', '?')}: could not sync")

    # Remove events for slots that no longer exist on the student's timetable
    # (e.g. they deleted a class or an elective changed).
    for key, event_id in existing.items():
        if key in seen_keys:
            continue
        try:
            resp = requests.delete(
                GOOGLE_EVENTS_URL.format(cal_id=CAL_ID) + f"/{event_id}",
                headers=hdrs, timeout=10,
            )
            if resp.status_code not in (200, 204, 404, 410):
                resp.raise_for_status()
            forget_synced_event(erp_id, key)
            removed += 1
        except requests.RequestException as e:
            logger.warning("Calendar cleanup failed for slot %s (erp_id=%s): %s", key, erp_id, e)
            errors.append("Could not remove one stale calendar event — it may need manual deletion.")

    return {"created": created, "updated": updated, "removed": removed, "errors": errors}


def unsync_all(erp_id: str) -> int:
    """Deletes every event AURA has ever created for this student (used by
    /calendar/timetable/sync DELETE and by full disconnect). Returns the
    count removed."""
    existing = get_synced_event_map(erp_id)
    # Bug 6 fix: fetch token once for the entire unsync operation.
    access_token = get_valid_access_token(erp_id)
    hdrs = _make_headers(access_token)
    removed = 0
    for key, event_id in existing.items():
        try:
            resp = requests.delete(
                GOOGLE_EVENTS_URL.format(cal_id=CAL_ID) + f"/{event_id}",
                headers=hdrs, timeout=10,
            )
            if resp.status_code not in (200, 204, 404, 410):
                resp.raise_for_status()
            forget_synced_event(erp_id, key)
            removed += 1
        except requests.RequestException as e:
            logger.warning("Failed to remove synced event %s for %s: %s", event_id, erp_id, e)
    return removed
