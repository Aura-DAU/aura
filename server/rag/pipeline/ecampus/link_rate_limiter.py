"""
SEC-04 fix: /ecampus/link previously had only the shared per-IP nginx
`aura_auth` zone (5 r/s, burst 10) in front of it. A student who controls
their own erp_id/JWT could still call this endpoint repeatedly, and each
call triggers a real eCampus scrape/credential-verify round trip against
an external system with no rate limiting of its own — a per-IP limit does
nothing to stop a single authenticated user from hammering it all day and
using AURA as a DoS amplifier against eCampus.

This is a small, dedicated fixed-window limiter keyed by erp_id (never by
IP — a student can always reach AURA from a new IP, but not get a new
erp_id). Deliberately separate from `rate_limiter.py`'s chat-quota store:
that store's window is anchored to the UTC calendar day, tuned for
guest/day question quotas; this one needs a short rolling hour window and
should never be affected by, or affect, chat-quota tuning.

Uses Redis (shared across workers) when REDIS_URL is set; otherwise an
in-memory fallback for single-process dev/tests.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Optional, Protocol

LINK_ATTEMPT_LIMIT = int(os.environ.get("ECAMPUS_LINK_RATE_LIMIT", "5"))
LINK_WINDOW_SECONDS = int(os.environ.get("ECAMPUS_LINK_RATE_WINDOW_SECONDS", str(60 * 60)))  # 1 hour


class EcampusLinkRateLimited(Exception):
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        super().__init__(
            f"Too many eCampus link attempts ({limit} per {window_seconds // 60} min). "
            "Please wait before trying again."
        )


class _LimiterStore(Protocol):
    def check_and_increment(self, key: str, limit: int, window_seconds: int) -> None: ...


@dataclass
class _Bucket:
    timestamps: list[float] = field(default_factory=list)

    def prune(self, now: float, window_seconds: int) -> None:
        cutoff = now - window_seconds
        self.timestamps = [t for t in self.timestamps if t > cutoff]


class InMemoryLinkRateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        self._buckets: dict[str, _Bucket] = {}

    def check_and_increment(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket())
            bucket.prune(now, window_seconds)
            if len(bucket.timestamps) >= limit:
                raise EcampusLinkRateLimited(limit=limit, window_seconds=window_seconds)
            bucket.timestamps.append(now)


class RedisLinkRateLimiter:
    """Fixed rolling window via a Redis sorted set, shared across workers."""

    def __init__(self, redis_url: str):
        import redis  # lazy — only required when REDIS_URL is configured

        self._r = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = os.environ.get("REDIS_ECAMPUS_LINK_PREFIX", "aura:ecampus_link:")

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def check_and_increment(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        cutoff = now - window_seconds
        rkey = self._key(key)
        member = f"{now}:{os.getpid()}"
        allowed = self._r.eval(
            """
            redis.call('ZREMRANGEBYSCORE', KEYS[1], 0, ARGV[1])
            local count = redis.call('ZCARD', KEYS[1])
            local limit = tonumber(ARGV[2])
            if count >= limit then
              return 0
            end
            redis.call('ZADD', KEYS[1], ARGV[3], ARGV[4])
            redis.call('EXPIRE', KEYS[1], ARGV[5])
            return 1
            """,
            1,
            rkey,
            cutoff,
            limit,
            now,
            member,
            window_seconds + 60,
        )
        if int(allowed) == 0:
            raise EcampusLinkRateLimited(limit=limit, window_seconds=window_seconds)


def _build_store() -> _LimiterStore:
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        return RedisLinkRateLimiter(redis_url)
    return InMemoryLinkRateLimiter()


_store: _LimiterStore = _build_store()


def reset_store_for_tests(store: Optional[_LimiterStore] = None) -> None:
    global _store
    _store = store if store is not None else InMemoryLinkRateLimiter()


def enforce_link_rate_limit(erp_id: str) -> None:
    """Raises EcampusLinkRateLimited if `erp_id` has exceeded
    LINK_ATTEMPT_LIMIT link attempts within LINK_WINDOW_SECONDS."""
    _store.check_and_increment(erp_id, LINK_ATTEMPT_LIMIT, LINK_WINDOW_SECONDS)
