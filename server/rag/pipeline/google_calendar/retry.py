"""
retry.py — production-grade retry decorator for Google Calendar API calls.

Google Calendar API can return:
  - 429 Too Many Requests   (rate limited — honour Retry-After header)
  - 500/502/503/504         (transient server errors — retry with backoff)
  - 403 with rateLimitExceeded (quota exhausted — treat like 429)

Design decisions (senior-engineer level):
  - Jitter on every backoff interval to prevent thundering herd when
    multiple students sync simultaneously.
  - Respect Google's Retry-After header when present.
  - Distinguish retryable errors (network/transient) from permanent ones
    (400 Bad Request, 401 Unauthorized) — never retry permanent failures.
  - Callable-based API: with_backoff(lambda: requests.post(...)) so the
    caller constructs the request lazily and it's re-executed on each attempt.
  - Structured logging on every retry so we can trace in prod.
"""

from __future__ import annotations

import logging
import random
import time
from typing import Callable

import requests

logger = logging.getLogger("aura.gcal.retry")

# HTTP status codes that are safe to retry
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

# Google-specific error reasons that are retryable even inside a 403
_RETRYABLE_REASONS = frozenset({"rateLimitExceeded", "userRateLimitExceeded"})


class MaxRetriesExceeded(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, last_exc: Exception, attempts: int) -> None:
        self.last_exc = last_exc
        self.attempts = attempts
        super().__init__(f"All {attempts} attempts failed. Last error: {last_exc}")


def _is_retryable(exc: Exception) -> bool:
    """Decide whether an exception should trigger a retry."""
    if isinstance(exc, requests.HTTPError):
        resp = exc.response
        if resp is None:
            return False
        if resp.status_code in _RETRYABLE_STATUS:
            return True
        # 403 with specific Google error reason is retryable
        if resp.status_code == 403:
            try:
                reason = resp.json().get("error", {}).get("errors", [{}])[0].get("reason", "")
                return reason in _RETRYABLE_REASONS
            except Exception:
                return False
        return False
    # Network-level transient failures
    if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
        return True
    return False


def _retry_after_seconds(exc: Exception, base_delay: float, attempt: int) -> float:
    """Compute how many seconds to wait before the next attempt."""
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        header = exc.response.headers.get("Retry-After")
        if header:
            try:
                return float(header)
            except ValueError:
                pass
    # Exponential backoff: base * 2^attempt, capped at 64 s, plus full jitter
    cap = min(base_delay * (2 ** attempt), 64.0)
    return random.uniform(0, cap)  # full jitter — avoids coordinated retries


def with_backoff(
    fn: Callable[[], requests.Response],
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    operation: str = "google_calendar_api",
) -> requests.Response:
    """
    Execute fn() with exponential backoff on transient failures.

    Args:
        fn:           Zero-argument callable that returns a requests.Response.
                      Must call raise_for_status() internally OR let the caller
                      do it — with_backoff only retries on HTTPError + network errs.
        max_attempts: Total attempts including the first. Default 4.
        base_delay:   Base wait in seconds. Actual wait uses full jitter.
        operation:    Name logged on retry for traceability.

    Returns:
        The first successful requests.Response.

    Raises:
        MaxRetriesExceeded: When all attempts are exhausted.
        Any non-retryable exception from fn() is re-raised immediately.
    """
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            resp = fn()
            # Raise for HTTP errors so _is_retryable can inspect the response
            resp.raise_for_status()
            return resp
        except Exception as exc:
            if not _is_retryable(exc):
                # Permanent failure — bubble up immediately, no retry
                logger.debug(
                    "[%s] Non-retryable error on attempt %d: %s",
                    operation, attempt + 1, exc,
                )
                raise

            last_exc = exc
            if attempt == max_attempts - 1:
                break  # exhausted — fall through to raise

            wait = _retry_after_seconds(exc, base_delay, attempt)
            status = getattr(getattr(exc, "response", None), "status_code", "network")
            logger.warning(
                "[%s] Attempt %d/%d failed (HTTP %s). Retrying in %.2fs...",
                operation, attempt + 1, max_attempts, status, wait,
            )
            time.sleep(wait)

    raise MaxRetriesExceeded(last_exc, max_attempts)
