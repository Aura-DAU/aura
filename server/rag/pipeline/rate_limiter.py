# Question quota enforcement — v7 policy: 3 questions/day for guest accounts,
# 5 questions/day for DAU accounts (student/faculty/admin), keyed by the
# before this handles production traffic on more than one process.

import time
import threading
from dataclasses import dataclass, field

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


@dataclass
class _Bucket:
    timestamps: list = field(default_factory=list)

    def prune(self, now: float):
        cutoff = now - QUOTA_WINDOW_SECONDS
        self.timestamps = [t for t in self.timestamps if t > cutoff]


class InMemoryQuotaStore:
    # Swap this class for a Postgres/Redis-backed store; interface only needs
    # check_and_increment(key, limit) -> remaining:int (raises QuotaExceeded).

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


_store = InMemoryQuotaStore()


def enforce_quota(quota_key: str, role: str) -> int:
    # Raises QuotaExceeded if the caller has hit their daily limit; otherwise
    # records this question and returns the remaining count. `quota_key`
    # guests share erp_id="GUEST".
    limit = QUOTA_LIMITS.get(role, QUOTA_LIMITS["guest"])
    return _store.check_and_increment(quota_key, limit)


def peek_remaining(quota_key: str, role: str) -> int:
    limit = QUOTA_LIMITS.get(role, QUOTA_LIMITS["guest"])
    return _store.remaining(quota_key, limit)
