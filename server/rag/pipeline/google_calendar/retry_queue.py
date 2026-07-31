"""
retry_queue.py — Automatic retry with Dead Letter Queue (DLQ).

When a slot sync fails (network blip, Google 503), we don't want the user to
have to manually re-trigger the whole sync. Instead:

  1. Failed slots go into gcal_retry_queue with next_retry = now + backoff.
  2. A background daemon thread polls every 60 s and processes due rows.
  3. After MAX_ATTEMPTS the row moves to gcal_dlq for manual investigation.
  4. The retry worker itself uses the same with_backoff() on the single API
     call, so each retry attempt also gets its own backoff on transient errors.

DLQ philosophy: DLQ rows are never automatically deleted. They're there for
the ops team to diagnose persistent failures (bad slot data, expired token,
calendar permission revoked, etc.) and replay manually if needed.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
import os
from typing import Any

import requests

from .client import get_valid_access_token
from .token_vault import _connect as _vault_connect
from .writer import _event_body, _EVENTS_URL, _make_headers
from .retry import with_backoff, MaxRetriesExceeded

logger = logging.getLogger("aura.gcal.retry_queue")

MAX_ATTEMPTS = 4
_RETRY_INTERVALS = [2, 8, 30, 120]  # minutes between retries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _next_retry_time(attempt: int) -> str:
    minutes = _RETRY_INTERVALS[min(attempt, len(_RETRY_INTERVALS) - 1)]
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def enqueue_failed_slots(
    erp_id: str,
    error_messages: list[str],
    all_slots: list[dict],
) -> None:
    """
    Queue failed slot payloads for retry. Called by sync_job.py when a sync
    completes but individual slots had errors.

    We match errors by course_code substring — good enough since slot identity
    is the erp_id + slot_key, not the error message.
    """
    # Build a lookup: course_code → slot
    slot_by_code: dict[str, dict] = {s.get("course_code", ""): s for s in all_slots}

    with _vault_connect() as conn:
        for err_msg in error_messages:
            # Try to find which slot this error belongs to
            matched_slot = None
            for code, slot in slot_by_code.items():
                if code and code in err_msg:
                    matched_slot = slot
                    break
            if matched_slot is None:
                continue
            slot_key = str(matched_slot.get("id", ""))
            if not slot_key:
                continue
            conn.execute(
                """
                INSERT INTO gcal_retry_queue
                  (erp_id, slot_key, payload, attempt, next_retry, last_error)
                VALUES (?, ?, ?, 0, ?, ?)
                ON CONFLICT DO NOTHING
                """,
                (erp_id, slot_key, json.dumps(matched_slot), _next_retry_time(0), err_msg),
            )


def _move_to_dlq(
    conn: sqlite3.Connection,
    row_id: int,
    erp_id: str,
    slot_key: str,
    payload: str,
    attempts: int,
    last_error: str,
) -> None:
    conn.execute(
        """
        INSERT INTO gcal_dlq (erp_id, slot_key, payload, attempts, last_error)
        VALUES (?, ?, ?, ?, ?)
        """,
        (erp_id, slot_key, payload, attempts, last_error),
    )
    conn.execute("DELETE FROM gcal_retry_queue WHERE id = ?", (row_id,))


def _process_due_retries() -> None:
    """Process all retry queue rows whose next_retry timestamp has passed."""
    now = _now_iso()
    with _vault_connect() as conn:
        due = conn.execute(
            """
            SELECT id, erp_id, slot_key, payload, attempt, last_error
            FROM gcal_retry_queue
            WHERE next_retry <= ?
            ORDER BY next_retry ASC
            LIMIT 50
            """,
            (now,),
        ).fetchall()

    for row in due:
        row_id, erp_id, slot_key, payload_str, attempt, last_error = (
            row["id"], row["erp_id"], row["slot_key"],
            row["payload"], row["attempt"], row["last_error"]
        )
        new_attempt = attempt + 1
        slot = json.loads(payload_str)

        if new_attempt > MAX_ATTEMPTS:
            with _vault_connect() as conn:
                _move_to_dlq(conn, row_id, erp_id, slot_key, payload_str, new_attempt, last_error or "")
            logger.error(
                "[retry_queue] Slot %s for %s exhausted %d attempts — moved to DLQ",
                slot_key, erp_id, MAX_ATTEMPTS,
            )
            continue

        try:
            access_token = get_valid_access_token(erp_id)
            hdrs = _make_headers(access_token)
            from .token_vault import get_preferences
            prefs = get_preferences(erp_id)
            cal_id = prefs.get("calendar_id", "primary")
            body = _event_body(slot, tz=prefs.get("timezone", "Asia/Kolkata"),
                               reminders=prefs.get("reminders", [30, 10]),
                               holidays=[], cal_id=cal_id)
            resp = with_backoff(
                lambda: requests.post(
                    _EVENTS_URL.format(cal_id=cal_id),
                    headers=hdrs, json=body, timeout=10,
                ),
                operation=f"retry_slot_{slot_key}",
            )
            from .token_vault import record_synced_event
            from .change_detector import slot_hash
            record_synced_event(erp_id, slot_key, resp.json().get("id", ""), slot_hash(slot))
            # Success — remove from retry queue
            with _vault_connect() as conn:
                conn.execute("DELETE FROM gcal_retry_queue WHERE id = ?", (row_id,))
            logger.info("[retry_queue] Slot %s for %s succeeded on attempt %d", slot_key, erp_id, new_attempt)

        except (MaxRetriesExceeded, requests.RequestException, Exception) as exc:
            err_str = str(exc)
            if new_attempt >= MAX_ATTEMPTS:
                with _vault_connect() as conn:
                    _move_to_dlq(conn, row_id, erp_id, slot_key, payload_str, new_attempt, err_str)
                logger.error(
                    "[retry_queue] Slot %s for %s → DLQ after %d attempts: %s",
                    slot_key, erp_id, new_attempt, err_str,
                )
            else:
                with _vault_connect() as conn:
                    conn.execute(
                        """
                        UPDATE gcal_retry_queue
                        SET attempt=?, next_retry=?, last_error=?
                        WHERE id=?
                        """,
                        (new_attempt, _next_retry_time(new_attempt), err_str, row_id),
                    )
                logger.warning(
                    "[retry_queue] Slot %s for %s failed (attempt %d/%d): %s. Next retry in %d min.",
                    slot_key, erp_id, new_attempt, MAX_ATTEMPTS, err_str,
                    _RETRY_INTERVALS[min(new_attempt, len(_RETRY_INTERVALS) - 1)],
                )


# ---------------------------------------------------------------------------
# Daemon thread — polls retry queue every 60 seconds
# ---------------------------------------------------------------------------

_retry_worker_started = False
_retry_worker_lock = threading.Lock()


def start_retry_worker() -> None:
    """
    Start the background retry daemon. Idempotent — safe to call on every
    server startup; only one thread is ever created.
    """
    global _retry_worker_started
    with _retry_worker_lock:
        if _retry_worker_started:
            return
        _retry_worker_started = True

    def _loop() -> None:
        import time
        while True:
            try:
                _process_due_retries()
            except Exception as exc:
                logger.error("[retry_queue] Worker loop error: %s", exc)
            time.sleep(60)

    t = threading.Thread(target=_loop, name="gcal-retry-worker", daemon=True)
    t.start()
    logger.info("[retry_queue] Background retry worker started.")
