# Encrypted per-faculty Google Calendar OAuth token storage.
# Each faculty member can optionally connect their Google Calendar.
# GOOGLE_CALENDAR_VAULT_DB     (SQLite path, default below)

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
    # Called by the OAuth callback handler after the user grants consent.
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