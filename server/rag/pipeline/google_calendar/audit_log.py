"""
audit_log.py — Append-only sync history log.

Every calendar-related action (sync, unsync, connect, disconnect, preview,
revoke) appends a row here. This table is NEVER deleted from — even after
a student disconnects, their history remains for support and debugging.

Fields:
  erp_id  — the student/faculty who performed the action
  action  — one of: connect | disconnect | sync | unsync | preview | revoke
  status  — success | failed | skipped | partial
  detail  — JSON payload (job_id, event counts, error messages, etc.)
  ts      — UTC ISO timestamp

Usage:
    from pipeline.google_calendar.audit_log import log_action
    log_action(erp_id, "sync", "success", {"job_id": "...", "created": 5})
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os

logger = logging.getLogger("aura.gcal.audit")

_DB_PATH = Path(os.environ.get("GOOGLE_CALENDAR_VAULT_DB", "/var/lib/aura/gcal_tokens.db"))


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(_DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_audit_log (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            erp_id  TEXT NOT NULL,
            action  TEXT NOT NULL,
            status  TEXT NOT NULL,
            detail  TEXT,
            ts      TEXT NOT NULL
        )
    """)
    # Index for fast per-user lookup
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_erp
        ON gcal_audit_log (erp_id, ts DESC)
    """)
    conn.commit()
    return conn


def log_action(
    erp_id: str,
    action: str,
    status: str,
    detail: dict[str, Any] | None = None,
) -> None:
    """
    Append a log entry. Never raises — audit failures must not block the
    user-facing operation (connection, sync, etc.).
    """
    try:
        with _connect() as conn:
            conn.execute(
                "INSERT INTO gcal_audit_log (erp_id, action, status, detail, ts) VALUES (?,?,?,?,?)",
                (
                    erp_id,
                    action,
                    status,
                    json.dumps(detail) if detail else None,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
    except Exception as exc:
        # Log to application logger but swallow — audit log failure must
        # never cause the primary operation to fail or return an error.
        logger.error("[audit] Failed to write audit entry for %s/%s: %s", erp_id, action, exc)


def get_history(erp_id: str, limit: int = 50) -> list[dict]:
    """
    Return the most recent audit entries for a student (newest first).
    Used by GET /calendar/audit endpoint.
    """
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, erp_id, action, status, detail, ts
            FROM gcal_audit_log
            WHERE erp_id = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (erp_id, limit),
        ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        if d.get("detail"):
            try:
                d["detail"] = json.loads(d["detail"])
            except (ValueError, TypeError):
                pass
        result.append(d)
    return result
