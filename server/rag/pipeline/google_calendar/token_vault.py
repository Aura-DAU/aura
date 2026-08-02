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

# Scope constants — exported and used by client.py, calendar_routes.py.
# VAULT_KEY and DB_PATH are intentionally NOT read at module import time —
# they are read lazily inside _fernet() and _connect() so that env vars
# set after import (e.g. in tests or deferred secrets managers) are
# always picked up correctly (Bug 8 fix).
SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
SCOPE_EVENTS   = "https://www.googleapis.com/auth/calendar.events"


class CalendarNotLinked(Exception):
    pass


def _fernet() -> Fernet:
    vault_key = os.environ.get("GOOGLE_CALENDAR_VAULT_KEY", "")
    if not vault_key:
        raise RuntimeError("GOOGLE_CALENDAR_VAULT_KEY is not set.")
    key = vault_key.encode() if isinstance(vault_key, str) else vault_key
    return Fernet(key)


def _connect():
    db_path = Path(os.environ.get("GOOGLE_CALENDAR_VAULT_DB",
                                   "/var/lib/aura/gcal_tokens.db"))
    # mode=0o700 restricts a vault dir AURA creates itself; it does not loosen
    # (or tighten) an already-existing shared parent such as /tmp.
    db_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(db_path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # ── Core token storage ────────────────────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_tokens (
            erp_id               TEXT PRIMARY KEY,
            encrypted_blob       BLOB NOT NULL,
            scope                TEXT NOT NULL DEFAULT 'https://www.googleapis.com/auth/calendar.readonly',
            linked_at            TEXT NOT NULL,
            -- User preferences (all nullable = use server default)
            preferred_calendar_id TEXT DEFAULT 'primary',
            preferred_timezone    TEXT DEFAULT 'Asia/Kolkata',
            sync_policy          TEXT DEFAULT 'overwrite',
            reminder_minutes     TEXT DEFAULT '30,10',
            exam_calendar_id     TEXT
        )
    """)

    # Idempotent migrations for databases created before preference columns
    # were added. SQLite doesn't support IF NOT EXISTS on ADD COLUMN, so we
    # use a try/except per column — harmless if it already exists.
    _add_column_if_missing(conn, "gcal_tokens", "preferred_calendar_id", "TEXT DEFAULT 'primary'")
    _add_column_if_missing(conn, "gcal_tokens", "preferred_timezone",    "TEXT DEFAULT 'Asia/Kolkata'")
    _add_column_if_missing(conn, "gcal_tokens", "sync_policy",           "TEXT DEFAULT 'overwrite'")
    _add_column_if_missing(conn, "gcal_tokens", "reminder_minutes",      "TEXT DEFAULT '30,10'")
    _add_column_if_missing(conn, "gcal_tokens", "exam_calendar_id",      "TEXT")

    # ── Synced event tracking ─────────────────────────────────────────────────
    # Maps (erp_id, slot_key) → google_event_id so re-syncs PATCH the same
    # event rather than creating a duplicate. slot_hash enables change
    # detection — we skip PATCH if the hash matches (no content change).
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_synced_events (
            erp_id          TEXT NOT NULL,
            slot_key        TEXT NOT NULL,
            google_event_id TEXT NOT NULL,
            slot_hash       TEXT,
            updated_at      TEXT NOT NULL,
            PRIMARY KEY (erp_id, slot_key)
        )
    """)
    _add_column_if_missing(conn, "gcal_synced_events", "slot_hash", "TEXT")

    # ── Retry queue ───────────────────────────────────────────────────────────
    # Failed individual slot syncs are queued here for automatic retry.
    # After max_attempts the row moves to gcal_dlq.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_retry_queue (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            erp_id      TEXT NOT NULL,
            slot_key    TEXT NOT NULL,
            payload     TEXT NOT NULL,
            attempt     INTEGER DEFAULT 0,
            next_retry  TEXT NOT NULL,
            last_error  TEXT
        )
    """)

    # ── Dead Letter Queue ─────────────────────────────────────────────────────
    # Slots that failed all retry attempts land here for manual investigation.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_dlq (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            erp_id      TEXT NOT NULL,
            slot_key    TEXT NOT NULL,
            payload     TEXT NOT NULL,
            attempts    INTEGER NOT NULL,
            last_error  TEXT,
            failed_at   TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── Webhook channels ──────────────────────────────────────────────────────
    # Google Watch API channel metadata (Phase 4 — two-way sync).
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_webhook_channels (
            erp_id      TEXT PRIMARY KEY,
            channel_id  TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            expiration  TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    # Restrict DB permissions (OAuth tokens are sensitive)
    try:
        os.chmod(db_path, 0o600)
    except OSError:
        pass
    conn.commit()
    return conn


def _add_column_if_missing(conn: sqlite3.Connection, table: str, column: str, defn: str) -> None:
    """Idempotent column migration for SQLite (no IF NOT EXISTS on ADD COLUMN)."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {defn}")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists


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

def get_synced_event_map(erp_id: str) -> dict[str, tuple[str, str | None]]:
    """Returns {slot_key: (google_event_id, slot_hash)} for everything AURA
    has previously written to this student's calendar.
    slot_hash may be None for events synced before change detection was added."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT slot_key, google_event_id, slot_hash FROM gcal_synced_events WHERE erp_id = ?",
            (erp_id,),
        ).fetchall()
    return {row[0]: (row[1], row[2]) for row in rows}


def record_synced_event(
    erp_id: str,
    slot_key: str,
    google_event_id: str,
    slot_hash: str | None = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """INSERT INTO gcal_synced_events
                 (erp_id, slot_key, google_event_id, slot_hash, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'))
               ON CONFLICT(erp_id, slot_key) DO UPDATE SET
                 google_event_id = excluded.google_event_id,
                 slot_hash       = excluded.slot_hash,
                 updated_at      = excluded.updated_at""",
            (erp_id, slot_key, google_event_id, slot_hash),
        )


def forget_synced_event(erp_id: str, slot_key: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM gcal_synced_events WHERE erp_id = ? AND slot_key = ?",
            (erp_id, slot_key),
        )


# ---------------------------------------------------------------------------
# User preference getters / setters
# ---------------------------------------------------------------------------

def get_preferences(erp_id: str) -> dict:
    """Return the user's stored calendar preferences with defaults."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT preferred_calendar_id, preferred_timezone,
                   sync_policy, reminder_minutes, exam_calendar_id
            FROM gcal_tokens WHERE erp_id = ?
            """,
            (erp_id,),
        ).fetchone()
    if not row:
        raise CalendarNotLinked(f"No calendar linked for {erp_id}")
    return {
        "calendar_id":    row[0] or "primary",
        "timezone":       row[1] or "Asia/Kolkata",
        "sync_policy":    row[2] or "overwrite",
        "reminders":      [int(m) for m in (row[3] or "30,10").split(",") if m.strip()],
        "exam_calendar_id": row[4],
    }


def update_preferences(erp_id: str, **kwargs: str | None) -> None:
    """
    Update one or more preference columns for an already-linked user.

    Accepted kwargs: calendar_id, timezone, sync_policy, reminder_minutes,
                     exam_calendar_id.
    Unknown kwargs are silently ignored for forward compatibility.
    """
    _ALLOWED = {
        "calendar_id":      "preferred_calendar_id",
        "timezone":         "preferred_timezone",
        "sync_policy":      "sync_policy",
        "reminder_minutes": "reminder_minutes",
        "exam_calendar_id": "exam_calendar_id",
    }
    updates = {_ALLOWED[k]: v for k, v in kwargs.items() if k in _ALLOWED}
    if not updates:
        return
    cols = ", ".join(f"{col} = ?" for col in updates)
    vals = list(updates.values()) + [erp_id]
    with _connect() as conn:
        conn.execute(f"UPDATE gcal_tokens SET {cols} WHERE erp_id = ?", vals)