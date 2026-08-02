"""
notifier.py — "your class starts in 10 minutes" push notifications.

Two pieces:
  1. send_push() — wraps pywebpush + VAPID signing to deliver one
     notification to one subscribed browser/device.
  2. run_scheduler_tick() — the per-minute job: for every student with an
     active push subscription, check whether they have a lecture or lab
     starting in REMINDER_MINUTES_BEFORE minutes, and if so, notify them
     exactly once (deduplicated via redis_client.set_if_not_exists, with a
     notification_log DB row as a durable backstop).

Wired into the FastAPI app lifespan in api/api.py — see start_scheduler()/
stop_scheduler(). Uses a plain asyncio background task rather than pulling
in APScheduler, since one job on one fixed interval doesn't need a full
scheduling library.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import logging
import os

import db.connection as db_conn
from .. import redis_client
from . import service

logger = logging.getLogger("aura.timetable.notifier")

REMINDER_MINUTES_BEFORE = int(os.environ.get("TIMETABLE_REMINDER_MINUTES", "10"))
SCHEDULER_INTERVAL_SECONDS = int(os.environ.get("TIMETABLE_SCHEDULER_INTERVAL_SECONDS", "60"))

VAPID_PRIVATE_KEY = os.environ.get("VAPID_PRIVATE_KEY", "")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY", "")
VAPID_CONTACT_EMAIL = os.environ.get("VAPID_CONTACT_EMAIL", "mailto:aura-admin@dau.ac.in")


def _get_active_subscriptions() -> list[dict]:
    return db_conn.query(
        """SELECT id, erp_id, endpoint, p256dh, auth_key
           FROM push_subscriptions WHERE is_active = TRUE""",
    )


def send_push(subscription: dict, title: str, body: str, url: str = "/dashboard") -> bool:
    """Sends one Web Push message. Returns False (and deactivates the
    subscription) if the push service reports it's gone (410/404)."""
    if not VAPID_PRIVATE_KEY:
        logger.warning("VAPID_PRIVATE_KEY not configured — skipping push send (dev/demo mode).")
        return False
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush not installed — run `pip install pywebpush` to enable push notifications.")
        return False

    payload = json.dumps({"title": title, "body": body, "url": url})
    try:
        webpush(
            subscription_info={
                "endpoint": subscription["endpoint"],
                "keys": {"p256dh": subscription["p256dh"], "auth": subscription["auth_key"]},
            },
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims={"sub": VAPID_CONTACT_EMAIL},
        )
        return True
    except WebPushException as e:
        status = getattr(e.response, "status_code", None)
        if status in (404, 410):
            db_conn.execute(
                "UPDATE push_subscriptions SET is_active = FALSE WHERE id = %s",
                (subscription["id"],),
            )
        else:
            logger.warning("Push send failed for subscription %s: %s", subscription["id"], e)
        return False


def _already_notified(erp_id: str, class_date: datetime.date, start_time: str, course_code: str) -> bool:
    """Fast path: Redis SETNX. Falls back to a durable UNIQUE constraint on
    notification_log if Redis isn't available or the process restarted."""
    key = f"aura:timetable_notif:{erp_id}:{class_date.isoformat()}:{start_time}:{course_code}"
    if redis_client.set_if_not_exists(key, ttl_seconds=6 * 3600):
        return False  # we're first — go ahead and send
    return True


def _record_sent(erp_id: str, class_date: datetime.date, start_time: str, course_code: str) -> None:
    try:
        db_conn.execute(
            """INSERT INTO notification_log (erp_id, class_date, start_time, course_code)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (erp_id, class_date, start_time, course_code) DO NOTHING""",
            (erp_id, class_date, start_time, course_code),
        )
    except Exception:
        logger.exception("Failed to write notification_log row (non-fatal — Redis dedup still applies).")


def run_scheduler_tick(now: datetime.datetime | None = None) -> int:
    """One tick: find every student with an active subscription who has a
    lecture/lab starting in REMINDER_MINUTES_BEFORE minutes, and notify
    them. Returns the number of notifications sent (for logging/tests)."""
    now = now or datetime.datetime.now()
    sent_count = 0

    # BUG-04 fix: the scheduler runs every minute with no day-of-week guard.
    # The academic calendar only has classes Mon–Fri; if a bad timetable
    # import ever produces a day_of_week=5/6 row (Sat/Sun), this tick would
    # otherwise notify every subscribed student every weekend for a class
    # that was never supposed to exist on that day.
    if now.weekday() >= 5:  # Saturday or Sunday
        return 0

    subscriptions_by_erp: dict[str, list[dict]] = {}
    for sub in _get_active_subscriptions():
        subscriptions_by_erp.setdefault(sub["erp_id"], []).append(sub)

    for erp_id, subs in subscriptions_by_erp.items():
        try:
            slots = service.find_slots_starting_in(erp_id, REMINDER_MINUTES_BEFORE, now=now)
        except Exception:
            logger.exception("Failed to resolve timetable for %s during scheduler tick.", erp_id)
            continue

        for slot in slots:
            if slot["session_type"] not in ("lecture", "lab"):
                continue
            if _already_notified(erp_id, now.date(), slot["start_time"], slot["course_code"]):
                continue

            title = f"{slot['session_type'].capitalize()} in {REMINDER_MINUTES_BEFORE} minutes"
            room = f" · {slot['room']}" if slot.get("room") else ""
            body = f"{slot['course_name']} ({slot['course_code']}) at {slot['start_time']}{room}"

            for sub in subs:
                if send_push(sub, title, body):
                    sent_count += 1
            _record_sent(erp_id, now.date(), slot["start_time"], slot["course_code"])

    return sent_count


_scheduler_task: asyncio.Task | None = None


async def _scheduler_loop():
    while True:
        try:
            await asyncio.to_thread(run_scheduler_tick)
        except Exception:
            logger.exception("Timetable notification scheduler tick failed.")
        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


def start_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task is None or _scheduler_task.done():
        _scheduler_task = asyncio.create_task(_scheduler_loop())
        logger.info(
            "Timetable notification scheduler started (every %ss, reminder %s min before class).",
            SCHEDULER_INTERVAL_SECONDS, REMINDER_MINUTES_BEFORE,
        )


def stop_scheduler() -> None:
    global _scheduler_task
    if _scheduler_task is not None:
        _scheduler_task.cancel()
        _scheduler_task = None
