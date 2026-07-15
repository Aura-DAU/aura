"""
Calendar reminder creation — advisory link generation, NOT a Calendar API write.

Important constraint: client.py requests only the
`calendar.readonly` OAuth scope (see client.py docstring), and v7 policy
directive #1 makes AURA read-only against every external system. That
means this tool must NOT call the Calendar API's events.insert endpoint —
doing so would need a write scope AURA isn't granted, and would violate
the read-only policy even if it were.

Instead, this tool builds a standard Google Calendar "quick add" deep link
(https://calendar.google.com/calendar/render?action=TEMPLATE&...). The
frontend opens this link in a new tab; Google's own UI handles the actual
event creation, with the user reviewing and confirming it themselves.
AURA never touches the user's calendar directly.

If write access is ever desired, that requires: (1) re-consenting users
under the `calendar.events` (or full `calendar`) scope, (2) a documented
policy exception to directive #1, and (3) a server-side audit-logged write
path — none of which exist today. Until then, this deep-link approach is
the only compliant way to offer "create a reminder" as a feature.
"""

import datetime
import urllib.parse

GOOGLE_CALENDAR_RENDER_URL = "https://calendar.google.com/calendar/render"


def _format_gcal_datetime(dt: datetime.datetime) -> str:
    # Google Calendar quick-add wants UTC, no separators: 20260715T093000Z
    return dt.strftime("%Y%m%dT%H%M%SZ")


def build_reminder_link(
    title: str,
    start: datetime.datetime,
    end: datetime.datetime | None = None,
    description: str = "",
    location: str = "",
) -> str:
    """
    Returns a Google Calendar 'quick add' URL. start/end should be timezone-aware
    UTC datetimes; if end is omitted, defaults to start + 30 minutes.
    """
    if end is None:
        end = start + datetime.timedelta(minutes=30)

    params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{_format_gcal_datetime(start)}/{_format_gcal_datetime(end)}",
    }
    if description:
        params["details"] = description
    if location:
        params["location"] = location

    return f"{GOOGLE_CALENDAR_RENDER_URL}?{urllib.parse.urlencode(params)}"


def handle_calendar_reminder_creation(identity, title: str, start_iso: str,
                                       end_iso: str | None = None,
                                       description: str = "", **kwargs) -> dict:
    """
    Tool handler: detects reminder intent (title + start time, parsed upstream
    by the query planner / classifier) and returns a confirmation payload
    containing a Google Calendar deep link — never writes to the calendar
    directly. The frontend renders this as a "Add to Google Calendar" button.
    """
    if not identity:
        raise PermissionError("Calendar reminders require a signed-in user.")

    try:
        start = datetime.datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return {"error": "Could not understand the reminder time. Please specify a date and time."}

    end = None
    if end_iso:
        try:
            end = datetime.datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            end = None

    link = build_reminder_link(title=title, start=start, end=end, description=description)

    return {
        "reminder_title": title,
        "start": start.isoformat(),
        "end": (end or (start + datetime.timedelta(minutes=30))).isoformat(),
        "calendar_link": link,
        "note": "AURA can't add this to your calendar directly — tap the link to confirm and save it yourself.",
    }
