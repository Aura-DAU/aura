"""
sync_job.py — Async background sync worker.

The /calendar/timetable/sync endpoint now returns immediately with a job_id
(HTTP 202 Accepted) instead of blocking until all Google API calls finish.
This module runs the actual sync in a background thread.

Architecture:
  ThreadPoolExecutor (max 4 workers) — one worker per erp_id syncing.
  sync_status.py    — job lifecycle DB (PENDING→RUNNING→COMPLETED/FAILED)
  retry_queue.py    — failed individual slots queued for automatic retry
  audit_log.py      — append-only log of every sync result

Why ThreadPoolExecutor rather than asyncio or Celery?
  - AURA's FastAPI server already runs in a single asyncio event loop.
  - Calendar API calls are blocking (requests library), so they'd block the
    event loop if run as coroutines. Offloading to threads is the correct
    pattern for this codebase without adding a full task queue system.
  - Celery or RQ would add operational complexity (Redis/RabbitMQ dependency)
    not justified for the current scale. If the user base grows to >10k
    students syncing simultaneously, move to Celery + Redis.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from .writer import sync_timetable, CalendarWriteError
from .sync_status import (
    create_job,
    mark_running,
    mark_completed,
    mark_failed,
    has_running_job,
)
from .audit_log import log_action
from .retry_queue import enqueue_failed_slots

logger = logging.getLogger("aura.gcal.sync_job")

_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="gcal-sync",
)


def enqueue_sync(
    erp_id: str,
    timetable_slots: list[dict],
    *,
    scope: str = "full",
    subject_code: str | None = None,
    holidays: list | None = None,
) -> str:
    """
    Schedule a sync job in the background. Returns the job_id immediately.

    Raises ValueError if a sync is already running for this student
    (prevents double-submit on slow connections).
    """
    if has_running_job(erp_id):
        raise ValueError(
            f"A sync job is already running for {erp_id}. "
            "Wait for it to complete before starting another."
        )

    job_id = create_job(erp_id, scope=scope, subject_code=subject_code)
    _executor.submit(
        _run_sync_job,
        job_id, erp_id, timetable_slots,
        scope, subject_code, holidays or [],
    )
    logger.info(
        "[sync_job] Enqueued job %s for %s (scope=%s)", job_id, erp_id, scope
    )
    return job_id


def _run_sync_job(
    job_id: str,
    erp_id: str,
    timetable_slots: list[dict],
    scope: str,
    subject_code: str | None,
    holidays: list,
) -> None:
    """Background worker — runs in a ThreadPoolExecutor thread."""
    mark_running(job_id)
    logger.info("[sync_job:%s] Starting sync for %s", job_id, erp_id)

    try:
        result = sync_timetable(
            erp_id,
            timetable_slots,
            holidays=holidays,
            scope=scope,
            subject_code=subject_code,
        )
    except CalendarWriteError as exc:
        mark_failed(job_id, errors=[str(exc)])
        log_action(erp_id, "sync", "failed", {"job_id": job_id, "error": str(exc)})
        logger.error("[sync_job:%s] CalendarWriteError for %s: %s", job_id, erp_id, exc)
        return
    except Exception as exc:
        mark_failed(job_id, errors=[f"Unexpected error: {exc}"])
        log_action(erp_id, "sync", "failed", {"job_id": job_id, "error": str(exc)})
        logger.exception("[sync_job:%s] Unexpected error for %s", job_id, erp_id)
        return

    # Queue individual slot errors for retry
    if result.get("errors"):
        enqueue_failed_slots(erp_id, result["errors"], timetable_slots)

    status = "partial" if result.get("errors") else "success"
    mark_completed(
        job_id,
        created=result.get("created", 0),
        updated=result.get("updated", 0),
        skipped=result.get("skipped", 0),
        removed=result.get("removed", 0),
        errors=result.get("errors"),
    )
    log_action(
        erp_id,
        "sync",
        status,
        {"job_id": job_id, **result},
    )
    logger.info(
        "[sync_job:%s] Completed for %s — created=%d updated=%d skipped=%d removed=%d errors=%d",
        job_id, erp_id,
        result.get("created", 0), result.get("updated", 0),
        result.get("skipped", 0), result.get("removed", 0),
        len(result.get("errors", [])),
    )
