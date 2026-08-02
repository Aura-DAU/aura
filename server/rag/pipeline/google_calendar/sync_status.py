"""
sync_status.py — Sync job lifecycle tracking.

Tracks the status of every calendar sync job so:
  - Students can poll "is my sync done yet?" after the async job is enqueued.
  - Operations team can see failure rates and debug stuck jobs.
  - We avoid running duplicate sync jobs for the same student.

Status state machine:
  PENDING → RUNNING → COMPLETED
                    ↘ FAILED
  (any state) → CANCELLED  (if student disconnects mid-sync)

Job record is keyed by UUID job_id. The latest job per erp_id is returned
by get_latest_status() for the "my sync status" frontend polling endpoint.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
import os
from typing import Literal

SyncState = Literal["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]

_DB_PATH = Path(os.environ.get("GOOGLE_CALENDAR_VAULT_DB", "/var/lib/aura/gcal_tokens.db"))


def _connect() -> sqlite3.Connection:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    conn = sqlite3.connect(_DB_PATH, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # WAL mode allows concurrent reads during writes — required when
    # sync_status, audit_log, and token_vault all write to the same DB.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gcal_sync_jobs (
            job_id       TEXT PRIMARY KEY,
            erp_id       TEXT NOT NULL,
            status       TEXT NOT NULL DEFAULT 'PENDING',
            scope        TEXT NOT NULL DEFAULT 'full',
            subject_code TEXT,
            triggered_at TEXT NOT NULL,
            started_at   TEXT,
            completed_at TEXT,
            created      INTEGER DEFAULT 0,
            updated      INTEGER DEFAULT 0,
            skipped      INTEGER DEFAULT 0,
            removed      INTEGER DEFAULT 0,
            errors       TEXT DEFAULT '[]'
        )
    """)
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_job(erp_id: str, scope: str = "full", subject_code: str | None = None) -> str:
    """Create a new PENDING job record. Returns the new job_id UUID."""
    job_id = str(uuid.uuid4())
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO gcal_sync_jobs
              (job_id, erp_id, status, scope, subject_code, triggered_at)
            VALUES (?, ?, 'PENDING', ?, ?, ?)
            """,
            (job_id, erp_id, scope, subject_code, _now_iso()),
        )
    return job_id


def mark_running(job_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE gcal_sync_jobs SET status='RUNNING', started_at=? WHERE job_id=?",
            (_now_iso(), job_id),
        )


def mark_completed(
    job_id: str,
    *,
    created: int = 0,
    updated: int = 0,
    skipped: int = 0,
    removed: int = 0,
    errors: list[str] | None = None,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE gcal_sync_jobs
            SET status='COMPLETED', completed_at=?,
                created=?, updated=?, skipped=?, removed=?, errors=?
            WHERE job_id=?
            """,
            (
                _now_iso(),
                created, updated, skipped, removed,
                json.dumps(errors or []),
                job_id,
            ),
        )


def mark_failed(job_id: str, errors: list[str]) -> None:
    with _connect() as conn:
        conn.execute(
            """
            UPDATE gcal_sync_jobs
            SET status='FAILED', completed_at=?, errors=?
            WHERE job_id=?
            """,
            (_now_iso(), json.dumps(errors), job_id),
        )


def mark_cancelled(job_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE gcal_sync_jobs SET status='CANCELLED', completed_at=? WHERE job_id=?",
            (_now_iso(), job_id),
        )


def get_job(job_id: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM gcal_sync_jobs WHERE job_id=?", (job_id,)
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["errors"] = json.loads(d.get("errors") or "[]")
    return d


def get_latest_job(erp_id: str) -> dict | None:
    """Return the most recently triggered job for this student."""
    with _connect() as conn:
        row = conn.execute(
            """
            SELECT * FROM gcal_sync_jobs
            WHERE erp_id=?
            ORDER BY triggered_at DESC
            LIMIT 1
            """,
            (erp_id,),
        ).fetchone()
    if not row:
        return None
    d = dict(row)
    d["errors"] = json.loads(d.get("errors") or "[]")
    return d


def has_running_job(erp_id: str) -> bool:
    """Guard against duplicate concurrent syncs for the same student."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM gcal_sync_jobs WHERE erp_id=? AND status IN ('PENDING','RUNNING')",
            (erp_id,),
        ).fetchone()
    return row is not None
