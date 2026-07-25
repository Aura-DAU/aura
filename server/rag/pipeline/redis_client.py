"""
redis_client.py — thin shared Redis helper.

AURA's architecture doc designates Redis as short-term memory (conversation
history) and, here, as the fast dedup layer for class-reminder notifications
("has this student already been notified about their 5 PM lecture today?").

Falls back to an in-memory store if REDIS_URL isn't configured, matching the
graceful-degradation style already used by rate_limiter.py's InMemoryQuotaStore
— this file stays usable in local/dev without a Redis container, but a real
Redis is expected in the deployed topology (aura-redis container).
"""

import os
import time
import threading
from typing import Optional

_redis = None
_redis_checked = False
_lock = threading.Lock()


def _get_redis():
    global _redis, _redis_checked
    if _redis_checked:
        return _redis
    with _lock:
        if _redis_checked:
            return _redis
        _redis_checked = True
        url = os.environ.get("REDIS_URL")
        if not url:
            _redis = None
            return None
        try:
            import redis  # type: ignore
            client = redis.from_url(url, decode_responses=True, socket_timeout=2)
            client.ping()
            _redis = client
        except Exception:
            _redis = None
    return _redis


class _InMemoryFallback:
    """Best-effort single-process substitute for the SETNX-with-TTL pattern."""

    def __init__(self):
        self._store: dict[str, float] = {}
        self._lock = threading.Lock()

    def set_if_not_exists(self, key: str, ttl_seconds: int) -> bool:
        now = time.time()
        with self._lock:
            expiry = self._store.get(key)
            if expiry is not None and expiry > now:
                return False
            self._store[key] = now + ttl_seconds
            return True


_fallback = _InMemoryFallback()


def set_if_not_exists(key: str, ttl_seconds: int) -> bool:
    """
    Atomically set `key` only if it doesn't already exist, with a TTL.
    Returns True if this call set it (i.e. "you're the first"), False if
    someone/something already set it (i.e. "already handled, skip").
    """
    client = _get_redis()
    if client is not None:
        try:
            return bool(client.set(key, "1", nx=True, ex=ttl_seconds))
        except Exception:
            pass
    return _fallback.set_if_not_exists(key, ttl_seconds)


def available() -> bool:
    return _get_redis() is not None
