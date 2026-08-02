"""Unit tests for RedisQuotaStore (mocked Redis client)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.rate_limiter import QuotaExceeded, RedisQuotaStore


def _make_store_with_fake_zset():
    """In-memory fake that mimics the sorted-set ops RedisQuotaStore uses."""
    zsets: dict[str, dict[str, float]] = {}

    class FakePipe:
        def __init__(self):
            self._ops = []

        def zremrangebyscore(self, key, min_score, max_score):
            self._ops.append(("zrem", key, min_score, max_score))
            return self

        def zcard(self, key):
            self._ops.append(("zcard", key))
            return self

        def zadd(self, key, mapping):
            self._ops.append(("zadd", key, mapping))
            return self

        def expire(self, key, ttl):
            self._ops.append(("expire", key, ttl))
            return self

        def execute(self):
            results = []
            for op in self._ops:
                kind = op[0]
                if kind == "zrem":
                    _, key, _min, max_score = op
                    bucket = zsets.setdefault(key, {})
                    for member, score in list(bucket.items()):
                        if score <= max_score:
                            del bucket[member]
                    results.append(0)
                elif kind == "zcard":
                    results.append(len(zsets.get(op[1], {})))
                elif kind == "zadd":
                    _, key, mapping = op
                    zsets.setdefault(key, {}).update(mapping)
                    results.append(len(mapping))
                elif kind == "expire":
                    results.append(True)
            self._ops.clear()
            return results

    client = MagicMock()
    client.pipeline.side_effect = lambda: FakePipe()

    def eval_script(_script, _numkeys, key, cutoff, limit, member, now, _ttl):
        bucket = zsets.setdefault(key, {})
        for existing_member, score in list(bucket.items()):
            if score <= cutoff:
                del bucket[existing_member]
        if len(bucket) >= limit:
            return [0, len(bucket)]
        bucket[member] = now
        return [1, len(bucket)]

    client.eval.side_effect = eval_script

    with patch("redis.Redis.from_url", return_value=client):
        store = RedisQuotaStore("redis://localhost:6379/0")
    return store


def test_redis_quota_allows_then_blocks():
    store = _make_store_with_fake_zset()
    assert store.check_and_increment("u@dau.ac.in", 3) == 2
    assert store.check_and_increment("u@dau.ac.in", 3) == 1
    assert store.check_and_increment("u@dau.ac.in", 3) == 0
    try:
        store.check_and_increment("u@dau.ac.in", 3)
        assert False, "expected QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.limit == 3
        assert exc.remaining == 0


def test_redis_quota_remaining_independent_keys():
    store = _make_store_with_fake_zset()
    store.check_and_increment("a@dau.ac.in", 5)
    assert store.remaining("b@dau.ac.in", 5) == 5
    assert store.remaining("a@dau.ac.in", 5) == 4
