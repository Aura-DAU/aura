"""
Google Calendar API client.

Wraps the Google Calendar API v3 token handling. Historically this module
only ever fetched events (faculty `calendar.readonly` grant, for
slot_service.py). As of v8 it also backs the student write flow in
writer.py / timetable_sync.py, which holds a `calendar.events` grant
instead — but token refresh is scope-agnostic, so `get_valid_access_token`
below is shared by both. This file itself still never calls a Calendar
API write endpoint; see writer.py for that.

Required env vars:
  GOOGLE_CALENDAR_CLIENT_ID
  GOOGLE_CALENDAR_CLIENT_SECRET
"""

import os
import time
import datetime
import requests

from .token_vault import get_tokens, store_tokens, CalendarNotLinked, SCOPE_READONLY

GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"
GOOGLE_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"

CLIENT_ID     = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")


def _refresh_access_token(erp_id: str, refresh_token: str) -> str:
    """Exchange the stored refresh token for a new access token."""
    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }, timeout=10)
    resp.raise_for_status()
    data       = resp.json()
    new_access = data["access_token"]
    expiry     = datetime.datetime.utcnow() + datetime.timedelta(
        seconds=data.get("expires_in", 3600)
    )
    # Persist the refreshed token — preserve the original scope so a
    # student's SCOPE_EVENTS grant isn't silently downgraded to SCOPE_READONLY.
    tokens = get_tokens(erp_id)
    store_tokens(erp_id, new_access, tokens["refresh_token"],
                 expiry.isoformat(), scope=tokens.get("scope", SCOPE_READONLY))
    return new_access


def _get_valid_access_token(erp_id: str) -> str:
    tokens = get_tokens(erp_id)
    expiry = datetime.datetime.fromisoformat(tokens["token_expiry"])
    # Refresh if expires within 5 minutes
    if datetime.datetime.utcnow() >= expiry - datetime.timedelta(minutes=5):
        return _refresh_access_token(erp_id, tokens["refresh_token"])
    return tokens["access_token"]


# Public alias — writer.py (student write flow) uses this name; kept the
# "_"-prefixed one too since slot_service.py already imports it that way.
get_valid_access_token = _get_valid_access_token


def get_events_on_date(erp_id: str, date: datetime.date) -> list[dict]:
    """
    Fetches all calendar events for a faculty member on a given date.
    Returns a list of {summary, start, end, is_busy} dicts.
    """
    access_token = _get_valid_access_token(erp_id)
    day_start    = datetime.datetime.combine(date, datetime.time.min).isoformat() + "Z"
    day_end      = datetime.datetime.combine(date, datetime.time.max).isoformat() + "Z"

    resp = requests.get(
        GOOGLE_EVENTS_URL.format(cal_id="primary"),
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "timeMin":      day_start,
            "timeMax":      day_end,
            "singleEvents": True,
            "orderBy":      "startTime",
        },
        timeout=10,
    )
    resp.raise_for_status()
    items = resp.json().get("items", [])
    return [
        {
            "summary":  item.get("summary", "(No title)"),
            "start":    item.get("start", {}).get("dateTime", item.get("start", {}).get("date")),
            "end":      item.get("end",   {}).get("dateTime", item.get("end",   {}).get("date")),
            "is_busy":  item.get("transparency", "opaque") != "transparent",
        }
        for item in items
    ]