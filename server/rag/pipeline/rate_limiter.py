"""
Question quota enforcement — v7 policy: 3 questions/day for guest accounts,
5 questions/day for DAU accounts (student/faculty/admin), keyed by the
signed-in Google account (email claim in the internal JWT, since guest
users all share erp_id="GUEST" and can't be distinguished by erp_id alone).

Uses Redis when REDIS_URL is set (shared across workers); otherwise an
in-memory store for single-process dev/tests.
"""

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Protocol

QUOTA_WINDOW_SECONDS = 24 * 60 * 60  # 24h rolling window

QUOTA_LIMITS = {
    "guest": 3,
    "student": 5,
    "faculty": 5,
    "admin": 5,
}


class QuotaExceeded(Exception):
    def __init__(self, limit: int, remaining: int = 0):
        self.limit = limit
        self.remaining = remaining
        super().__init__(f"Question limit reached ({limit}/day).")


class QuotaStore(Protocol):
    def check_and_increment(self, key: str, limit: int) -> int: ...
    def remaining(self, key: str, limit: int) -> int: ...


@dataclass
class _Bucket:
    timestamps: list = field(default_factory=list)

    def prune(self, now: float):
        cutoff = now - QUOTA_WINDOW_SECONDS
        self.timestamps = [t for t in self.timestamps if t > cutoff]


class InMemoryQuotaStore:
    """Swap this class for a Postgres/Redis-backed store; interface only needs
    check_and_increment(key, limit) -> remaining:int (raises QuotaExceeded)."""

    def __init__(self):
        self._buckets: dict[str, _Bucket] = {}
        self._lock = threading.Lock()

    def check_and_increment(self, key: str, limit: int) -> int:
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket())
            bucket.prune(now)
            if len(bucket.timestamps) >= limit:
                raise QuotaExceeded(limit=limit, remaining=0)
            bucket.timestamps.append(now)
            return max(0, limit - len(bucket.timestamps))

    def remaining(self, key: str, limit: int) -> int:
        now = time.time()
        with self._lock:
            bucket = self._buckets.setdefault(key, _Bucket())
            bucket.prune(now)
            return max(0, limit - len(bucket.timestamps))


class RedisQuotaStore:
    """Sliding 24h window via Redis sorted sets — shared across workers."""

    def __init__(self, redis_url: str):
        import redis  # lazy — only required when REDIS_URL is configured

        self._r = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = os.environ.get("REDIS_QUOTA_PREFIX", "aura:quota:")

    def _key(self, key: str) -> str:
        return f"{self._prefix}{key}"

    def check_and_increment(self, key: str, limit: int) -> int:
        now = time.time()
        cutoff = now - QUOTA_WINDOW_SECONDS
        rkey = self._key(key)
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(rkey, 0, cutoff)
        pipe.zcard(rkey)
        _, count = pipe.execute()
        if count >= limit:
            raise QuotaExceeded(limit=limit, remaining=0)
        member = f"{now}:{os.getpid()}:{id(object())}"
        pipe = self._r.pipeline()
        pipe.zadd(rkey, {member: now})
        pipe.expire(rkey, QUOTA_WINDOW_SECONDS + 60)
        pipe.zcard(rkey)
        _, _, new_count = pipe.execute()
        return max(0, limit - int(new_count))

    def remaining(self, key: str, limit: int) -> int:
        now = time.time()
        cutoff = now - QUOTA_WINDOW_SECONDS
        rkey = self._key(key)
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(rkey, 0, cutoff)
        pipe.zcard(rkey)
        _, count = pipe.execute()
        return max(0, limit - int(count))


def _build_store() -> QuotaStore:
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        return RedisQuotaStore(redis_url)
    return InMemoryQuotaStore()


_store: QuotaStore = _build_store()


def reset_store_for_tests(store: Optional[QuotaStore] = None) -> None:
    """Test helper — swap the module singleton."""
    global _store
    _store = store if store is not None else InMemoryQuotaStore()


def enforce_quota(quota_key: str, role: str) -> int:
    """
    Raises QuotaExceeded if the caller has hit their daily limit; otherwise
    records this question and returns the remaining count. `quota_key`
    should be the signed-in Google account email — never erp_id, since all
    guests share erp_id="GUEST".
    """
    limit = QUOTA_LIMITS.get(role, QUOTA_LIMITS["guest"])
    return _store.check_and_increment(quota_key, limit)


def peek_remaining(quota_key: str, role: str) -> int:
    limit = QUOTA_LIMITS.get(role, QUOTA_LIMITS["guest"])
    return _store.remaining(quota_key, limit)
