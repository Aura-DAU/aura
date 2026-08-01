"""
scheduler.py — Nightly auto-sync cron for Google Calendar.

Runs at 2 AM every night (configurable via GCAL_AUTO_SYNC_HOUR env var).
For every student who has calendar linked with write scope, triggers a
background sync to pick up any timetable_master changes made during the day.

Integration:
  Called from server/main.py (or app lifespan) on startup:

    from pipeline.google_calendar.scheduler import start_scheduler
    start_scheduler()

  Also starts the retry worker (idempotent — safe to call multiple times).

Design note:
  Uses a simple threading.Timer-based scheduler rather than APScheduler to
  avoid an extra dependency. If APScheduler is already in requirements,
  uncomment the APScheduler block below and delete the threading.Timer block.
"""

from __future__ import annotations

import logging
import os
import threading
from datetime import datetime, timezone

logger = logging.getLogger("aura.gcal.scheduler")

_AUTO_SYNC_HOUR = int(os.environ.get("GCAL_AUTO_SYNC_HOUR", "2"))  # default 2 AM UTC


def _seconds_until_next_run(hour: int) -> float:
    """Compute seconds until the next occurrence of `hour:00 UTC`."""
    now = datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        from datetime import timedelta
        target += timedelta(days=1)
    return (target - now).total_seconds()


def _run_nightly_sync() -> None:
    """
    Called once per night. Iterates all linked students with write scope
    and enqueues a full sync for each. Errors per-student are logged but
    do not stop other students from syncing.
    """
    logger.info("[scheduler] Nightly auto-sync starting.")
    try:
        from .token_vault import _connect as _vault_connect, SCOPE_EVENTS
        from pipeline.timetable.service import _CohortLookup, get_effective_timetable
        from pipeline.timetable import service as timetable_service
        from .sync_job import enqueue_sync
        import db.connection as db_conn

        with _vault_connect() as conn:
            rows = conn.execute(
                "SELECT erp_id FROM gcal_tokens WHERE scope = ?",
                (SCOPE_EVENTS,),
            ).fetchall()

        synced = 0
        for row in rows:
            erp_id = row[0]
            try:
                # Resolve cohort from DB so we build the correct timetable
                identity_rows = db_conn.query(
                    """
                    SELECT current_year, current_sem, current_sec
                    FROM user_identity_map
                    WHERE erp_id = %s AND is_active = TRUE
                    LIMIT 1
                    """,
                    (erp_id,),
                )
                if not identity_rows:
                    logger.debug(
                        "[scheduler] No identity_map row for %s — skipping auto-sync.", erp_id
                    )
                    continue

                r = identity_rows[0]
                cohort = _CohortLookup(
                    role="student",
                    erp_id=erp_id,
                    current_year=r.get("current_year") or 1,
                    current_sem=r.get("current_sem") or 1,
                    current_sec=r.get("current_sec") or "A",
                )
                effective = get_effective_timetable(cohort)
                slots = effective.get("timetable", [])
                if slots:
                    enqueue_sync(erp_id, slots, scope="full")
                    synced += 1
            except ValueError:
                # Already has a running job — skip
                pass
            except Exception as exc:
                logger.error("[scheduler] Auto-sync failed for %s: %s", erp_id, exc)

        logger.info("[scheduler] Nightly auto-sync enqueued %d students.", synced)
    except Exception as exc:
        logger.exception("[scheduler] Nightly sync runner crashed: %s", exc)
    finally:
        # Schedule the next run
        _schedule_next()


def _schedule_next() -> None:
    delay = _seconds_until_next_run(_AUTO_SYNC_HOUR)
    t = threading.Timer(delay, _run_nightly_sync)
    t.name = "gcal-nightly-sync"
    t.daemon = True
    t.start()
    logger.info(
        "[scheduler] Next auto-sync scheduled in %.0f seconds (at UTC %02d:00).",
        delay, _AUTO_SYNC_HOUR,
    )


_scheduler_started = False
_scheduler_lock = threading.Lock()


def start_scheduler() -> None:
    """
    Start the nightly auto-sync scheduler and the retry worker daemon.
    Idempotent — safe to call multiple times (only the first call takes effect).
    """
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True

    from .retry_queue import start_retry_worker
    start_retry_worker()
    _schedule_next()
    logger.info("[scheduler] Google Calendar scheduler and retry worker started.")
