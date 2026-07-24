"""
Encrypted per-user Google Calendar OAuth token storage.

v8 update: this now serves TWO distinct grants, both stored in the same
encrypted vault, disambiguated by the `scope` column:

  - FACULTY, read-only: `calendar.readonly` — used by slot_service.py to
    derive faculty availability windows for student booking. Unchanged
    from the original design: AURA never writes to a faculty calendar.

  - STUDENTS, read/write: `calendar.events` — used by timetable_sync.py
    to create/update/delete the student's own class events in their own
    Google Calendar, at their explicit request (OAuth consent screen
    names the exact scope Google grants; the student sees and approves
    "create and edit events" before anything is written). See writer.py
    for the only module in this package that performs write calls.

Every write call in writer.py is scoped to the identity.erp_id taken from
the verified internal JWT — a student can only ever hold a token for, and
sync events into, their OWN Google account, by construction (same
invariant as pipeline/timetable/service.py).

Setup checklist (IT team):
  1. Create a Google Cloud project.
  2. Enable the Google Calendar API.
  3. Create OAuth 2.0 credentials (Web application type).
  4. Add the redirect URI:
       https://aura.dau.ac.in/api/calendar/callback
  5. Set env vars:
       GOOGLE_CALENDAR_CLIENT_ID
       GOOGLE_CALENDAR_CLIENT_SECRET
       GOOGLE_CALENDAR_VAULT_KEY    (Fernet key — separate from ECAMPUS_VAULT_KEY)
       GOOGLE_CALENDAR_VAULT_DB     (SQLite path, default below)
       GOOGLE_CALENDAR_SEMESTER_END (YYYY-MM-DD — bounds the recurring
                                      timetable events; see timetable_sync.py)
"""

import os
import json
import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet

VAULT_KEY = os.environ.get("GOOGLE_CALENDAR_VAULT_KEY", "")
DB_PATH   = Path(os.environ.get("GOOGLE_CALENDAR_VAULT_DB",
                                 "/var/lib/aura/gcal_tokens.db"))

SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
SCOPE_EVENTS   = "https://www.googleapis.com/auth/calendar.events"


class CalendarNotLinked(Exception):
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
            scope           TEXT NOT NULL DEFAULT 'https://www.googleapis.com/auth/calendar.readonly',
            linked_at       TEXT NOT NULL
        )
    """)
    # Tracks every event AURA has created on a student's calendar, keyed by
    # the stable "slot key" (master row id, or override id for custom
    # entries) so a re-sync updates the same event in place instead of
    # duplicating it, and disconnect/unsync can clean everything up.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_synced_events (
            erp_id          TEXT NOT NULL,
            slot_key        TEXT NOT NULL,
            google_event_id TEXT NOT NULL,
            updated_at      TEXT NOT NULL,
            PRIMARY KEY (erp_id, slot_key)
        )
    """)
    return conn


def store_tokens(erp_id: str, access_token: str, refresh_token: str,
                  token_expiry: str, scope: str = SCOPE_READONLY) -> None:
    """Called by the OAuth callback handler after the user grants consent."""
    blob = json.dumps({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "token_expiry":  token_expiry,
    }).encode()
    encrypted = _fernet().encrypt(blob)
    with _connect() as conn:
        conn.execute(
            """INSERT INTO gcal_tokens (erp_id, encrypted_blob, scope, linked_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(erp_id) DO UPDATE SET
                 encrypted_blob = excluded.encrypted_blob,
                 scope          = excluded.scope,
                 linked_at      = excluded.linked_at""",
            (erp_id, encrypted, scope),
        )


def get_tokens(erp_id: str) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT encrypted_blob, scope FROM gcal_tokens WHERE erp_id = ?",
            (erp_id,),
        ).fetchone()
    if not row:
        raise CalendarNotLinked(
            f"No Google Calendar linked for {erp_id}. "
            "Ask the user to connect their calendar first."
        )
    decrypted = _fernet().decrypt(row[0])
    data = json.loads(decrypted)
    data["scope"] = row[1]
    return data


def get_scope(erp_id: str) -> str | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT scope FROM gcal_tokens WHERE erp_id = ?", (erp_id,)
        ).fetchone()
    return row[0] if row else None


def has_write_scope(erp_id: str) -> bool:
    return get_scope(erp_id) == SCOPE_EVENTS


def unlink_calendar(erp_id: str) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM gcal_tokens WHERE erp_id = ?", (erp_id,))
        conn.execute("DELETE FROM gcal_synced_events WHERE erp_id = ?", (erp_id,))


def is_linked(erp_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM gcal_tokens WHERE erp_id = ?", (erp_id,)
        ).fetchone()
    return row is not None


# --- synced-event tracking (student write flow only) -----------------------

def get_synced_event_map(erp_id: str) -> dict[str, str]:
    """slot_key -> google_event_id for everything AURA has previously
    written to this student's calendar."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slot_key, google_event_id FROM gcal_synced_events WHERE erp_id = ?",
            (erp_id,),
        ).fetchall()
    return {slot_key: event_id for slot_key, event_id in rows}


def record_synced_event(erp_id: str, slot_key: str, google_event_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO gcal_synced_events (erp_id, slot_key, google_event_id, updated_at)
               VALUES (?, ?, ?, datetime('now'))
               ON CONFLICT(erp_id, slot_key) DO UPDATE SET
                 google_event_id = excluded.google_event_id,
                 updated_at      = excluded.updated_at""",
            (erp_id, slot_key, google_event_id),
        )


def forget_synced_event(erp_id: str, slot_key: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM gcal_synced_events WHERE erp_id = ? AND slot_key = ?",
            (erp_id, slot_key),
        )