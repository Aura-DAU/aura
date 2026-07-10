"""
Encrypted per-faculty Google Calendar OAuth token storage.

Each faculty member can optionally connect their Google Calendar.
After completing the OAuth 2.0 authorization code flow, the access_token
and refresh_token are stored here — encrypted with Fernet (AES-128-CBC),
same pattern as pipeline/ecampus/credentials_vault.py.

Originally AURA only ever READ calendar data on the faculty's behalf —
scope requested: calendar.readonly. The reminder-creation tool (see
ecampus/tool_registry.py: create_calendar_reminder) needs to WRITE events,
which requires the stricter `calendar.events` scope below. Any token
obtained under the old readonly-only consent screen will be rejected by
Google with a 403 on event creation — faculty must re-link their calendar
after the IT team enables the broader scope (see client.CalendarWriteScopeMissing).

Setup checklist (IT team):
  1. Create a Google Cloud project.
  2. Enable the Google Calendar API.
  3. Create OAuth 2.0 credentials (Web application type).
  4. Add the redirect URI:
       https://aura.dau.ac.in/api/calendar/callback
  5. Request BOTH scopes on the consent screen so slot-fetching and
     reminder-creation both work for the same linked account:
       https://www.googleapis.com/auth/calendar.readonly
       https://www.googleapis.com/auth/calendar.events
  6. Set env vars:
       GOOGLE_CALENDAR_CLIENT_ID
       GOOGLE_CALENDAR_CLIENT_SECRET
       GOOGLE_CALENDAR_VAULT_KEY    (Fernet key — separate from ECAMPUS_VAULT_KEY)
       GOOGLE_CALENDAR_VAULT_DB     (SQLite path, default below)
"""

READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
EVENTS_SCOPE = "https://www.googleapis.com/auth/calendar.events"

import os
import json
import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet

VAULT_KEY = os.environ.get("GOOGLE_CALENDAR_VAULT_KEY", "")
DB_PATH   = Path(os.environ.get("GOOGLE_CALENDAR_VAULT_DB",
                                 "/var/lib/aura/gcal_tokens.db"))


class CalendarNotLinked(Exception):
    pass


class CalendarWriteScopeMissing(Exception):
    """Raised when Google rejects a write (event-creation) call because the
    stored token was only ever granted the calendar.readonly scope."""
    pass


def _fernet() -> Fernet:
    if not VAULT_KEY:
        raise RuntimeError("GOOGLE_CALENDAR_VAULT_KEY is not set.")
    key = VAULT_KEY.encode() if isinstance(VAULT_KEY, str) else VAULT_KEY
    return Fernet(key)


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_tokens (
            erp_id          TEXT PRIMARY KEY,
            encrypted_blob  BLOB NOT NULL,
            linked_at       TEXT NOT NULL
        )
    """)
    return conn


def store_tokens(erp_id: str, access_token: str, refresh_token: str,
                 token_expiry: str) -> None:
    """Called by the OAuth callback handler after the user grants consent."""
    blob = json.dumps({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_expiry":  token_expiry,
    }).encode()
    encrypted = _fernet().encrypt(blob)
    with _connect() as conn:
        conn.execute(
            """INSERT INTO gcal_tokens (erp_id, encrypted_blob, linked_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(erp_id) DO UPDATE SET
                 encrypted_blob = excluded.encrypted_blob,
                 linked_at      = excluded.linked_at""",
            (erp_id, encrypted),
        )


def get_tokens(erp_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT encrypted_blob FROM gcal_tokens WHERE erp_id = ?",
            (erp_id,),
        ).fetchone()
    if not row:
        raise CalendarNotLinked(
            f"No Google Calendar linked for {erp_id}. "
            "Ask the faculty member to connect their calendar first."
        )
    decrypted = _fernet().decrypt(row[0])
    return json.loads(decrypted)


def unlink_calendar(erp_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM gcal_tokens WHERE erp_id = ?", (erp_id,))


def is_linked(erp_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM gcal_tokens WHERE erp_id = ?", (erp_id,)
        ).fetchone()
    return row is not None