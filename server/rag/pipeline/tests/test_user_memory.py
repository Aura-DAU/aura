import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.memory.user_memory import (
    DEFAULT_USER_MEMORY_TTL_SECONDS,
    InMemoryUserMemoryStore,
    RedisUserMemoryStore,
    _identity_key,
    _merge_memory,
)


def test_user_memory_merges_thread_summaries_for_signed_in_user():
    store = InMemoryUserMemoryStore()
    identity = {
        "role": "student",
        "email": "student@dau.ac.in",
        "erp_id": "202401001",
    }

    assert store.get(identity) == ""
    store.merge(identity, "User prefers concise answers.", thread_id="t1")
    store.merge(identity, "User is working on timetable questions.", thread_id="t2")

    memory = store.get(identity)
    assert "User prefers concise answers." in memory
    assert "User is working on timetable questions." in memory
    # Two distinct conversations → two distinct blocks.
    assert memory.count("## Prior Thread Memory") == 2

    # Re-touching an existing thread updates its block in place, not appends.
    store.merge(identity, "User prefers concise answers, with examples.", thread_id="t1")
    memory = store.get(identity)
    assert memory.count("## Prior Thread Memory") == 2
    assert "with examples." in memory


def test_user_memory_ignores_guest_identity():
    store = InMemoryUserMemoryStore()
    guest = {"role": "guest", "erp_id": "GUEST-123"}

    assert _identity_key(guest) is None
    assert store.merge(guest, "Do not persist this.") == ""
    assert store.get(guest) == ""


def test_identity_key_prefers_stable_erp_id_over_email():
    with_email = {
        "role": "student",
        "email": "student@dau.ac.in",
        "erp_id": "202401001",
    }
    without_email = {
        "role": "student",
        "erp_id": "202401001",
    }

    assert _identity_key(with_email) == _identity_key(without_email)


def test_merge_replaces_evolving_summary_for_same_thread():
    existing = _merge_memory("", "User is comparing electives.", thread_id="t1")
    merged = _merge_memory(
        existing,
        "User is comparing electives and wants a timetable-safe option.",
        thread_id="t1",
    )

    assert "timetable-safe option" in merged
    assert merged.count("## Prior Thread Memory") == 1
    # The stale block for this thread is gone, not kept alongside the new one.
    assert "electives.\n" not in merged


def test_get_excludes_current_thread_and_orders_newest_first():
    store = InMemoryUserMemoryStore()
    identity = {"role": "student", "erp_id": "202401001"}

    store.merge(identity, "Asked about hostel fees.", thread_id="t1")
    store.merge(identity, "Asked about elective clashes.", thread_id="t2")

    # The active thread's own block is excluded (it's already in the live prompt
    # as the thread summary + tail), so it is never double-injected.
    injected = store.get(identity, exclude_thread="t2")
    assert "hostel fees" in injected
    assert "elective clashes" not in injected

    # Most recently touched conversation is injected first (recency-correct).
    full = store.get(identity)
    assert full.index("elective clashes") < full.index("hostel fees")


def test_redis_user_memory_get_soft_fails_when_redis_is_down():
    import redis

    client = MagicMock()
    client.get.side_effect = redis.RedisError("redis down")
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    assert store.get({"role": "student", "erp_id": "202401001"}) == ""


def test_redis_user_memory_merge_soft_fails_when_redis_is_down():
    import redis

    client = MagicMock()
    client.pipeline.side_effect = redis.RedisError("redis down")
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    assert store.merge({"role": "student", "erp_id": "202401001"}, "summary") == ""


def test_redis_user_memory_sets_retention_ttl():
    class FakePipe:
        def __init__(self):
            self.set_calls = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def watch(self, _key):
            return None

        def get(self, _key):
            return ""

        def multi(self):
            return None

        def set(self, key, value, ex=None):
            self.set_calls.append((key, value, ex))

        def execute(self):
            return [True]

    pipe = FakePipe()
    client = MagicMock()
    client.pipeline.return_value = pipe
    client.get.return_value = ""
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    store.merge({"role": "student", "erp_id": "202401001"}, "summary")

    assert pipe.set_calls
    assert pipe.set_calls[0][2] == DEFAULT_USER_MEMORY_TTL_SECONDS


def test_delete_removes_one_thread_and_preserves_siblings():
    store = InMemoryUserMemoryStore()
    identity = {"role": "student", "erp_id": "202401001"}

    store.merge(identity, "Asked about hostel fees.", thread_id="t1")
    store.merge(identity, "Asked about elective clashes.", thread_id="t2")

    assert store.delete(identity, "t1") is True
    memory = store.get(identity)
    assert "hostel fees" not in memory
    assert "elective clashes" in memory
    assert memory.count("## Prior Thread Memory") == 1

    # Idempotent: deleting an already-gone thread is a no-op, not an error.
    assert store.delete(identity, "t1") is False
    assert "elective clashes" in store.get(identity)


def test_delete_all_clears_identity():
    store = InMemoryUserMemoryStore()
    identity = {"role": "student", "erp_id": "202401001"}
    other = {"role": "student", "erp_id": "202401002"}

    store.merge(identity, "Mine.", thread_id="t1")
    store.merge(other, "Theirs.", thread_id="t9")

    assert store.delete_all(identity) is True
    assert store.get(identity) == ""
    assert "Theirs." in store.get(other)
    assert store.delete_all(identity) is False


def test_delete_is_noop_for_guest_and_empty_thread_id():
    store = InMemoryUserMemoryStore()
    guest = {"role": "guest", "erp_id": "GUEST-123"}
    student = {"role": "student", "erp_id": "202401001"}

    store.merge(student, "Keep me.", thread_id="t1")
    assert store.delete(guest, "t1") is False
    assert store.delete_all(guest) is False
    assert store.delete(student, "") is False
    assert "Keep me." in store.get(student)


def test_delete_memory_helper_filters_by_thread_id():
    from pipeline.memory.user_memory import _delete_memory

    existing = _merge_memory("", "Alpha.", thread_id="a")
    existing = _merge_memory(existing, "Beta.", thread_id="b")

    remaining, removed = _delete_memory(existing, "a")
    assert removed is True
    assert "Alpha." not in remaining
    assert "Beta." in remaining
    assert "(tid: b)" in remaining

    remaining2, removed2 = _delete_memory(remaining, "missing")
    assert removed2 is False
    assert remaining2 == remaining


def test_redis_delete_uses_watch_and_preserves_ttl():
    """Concurrent-safe rewrite: WATCH the key, rewrite without the target
    block, and keep the remaining TTL instead of restarting the 90-day clock."""
    existing = _merge_memory("", "Alpha.", thread_id="a")
    existing = _merge_memory(existing, "Beta.", thread_id="b")

    class FakePipe:
        def __init__(self):
            self.set_calls = []
            self.delete_calls = []
            self.unwatch_calls = 0
            self._value = existing

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def watch(self, _key):
            return None

        def get(self, _key):
            return self._value

        def ttl(self, _key):
            return 12_345

        def multi(self):
            return None

        def set(self, key, value, ex=None):
            self.set_calls.append((key, value, ex))
            self._value = value

        def delete(self, key):
            self.delete_calls.append(key)
            self._value = ""

        def unwatch(self):
            self.unwatch_calls += 1

        def execute(self):
            return [True]

    pipe = FakePipe()
    client = MagicMock()
    client.pipeline.return_value = pipe
    client.get.side_effect = lambda _key: pipe._value
    client.ttl.return_value = 12_345
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    assert store.delete({"role": "student", "erp_id": "202401001"}, "a") is True
    assert pipe.set_calls
    key, value, ex = pipe.set_calls[0]
    assert "Alpha." not in value
    assert "Beta." in value
    assert ex == 12_345  # remaining TTL preserved, not the default 90-day reset
    assert not pipe.delete_calls

    # Missing thread → unwatch, no write.
    pipe.set_calls.clear()
    assert store.delete({"role": "student", "erp_id": "202401001"}, "missing") is False
    assert pipe.unwatch_calls == 1
    assert not pipe.set_calls


def test_redis_delete_retries_on_watch_error():
    """A concurrent merge/delete racing on the same key must not lose the other
    writer's update — WatchError forces a re-read and rewrite."""
    import redis

    existing = _merge_memory("", "Alpha.", thread_id="a")
    existing = _merge_memory(existing, "Beta.", thread_id="b")

    class FlakyPipe:
        def __init__(self):
            self.attempts = 0
            self.set_calls = []
            self._value = existing
            self._pending = None

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def watch(self, _key):
            return None

        def get(self, _key):
            return self._value

        def ttl(self, _key):
            return -1

        def multi(self):
            return None

        def set(self, key, value, ex=None):
            # Buffer until execute() commits — mirrors redis-py MULTI/EXEC.
            self._pending = (key, value, ex)

        def delete(self, key):
            self._pending = ("__del__", key, None)

        def unwatch(self):
            return None

        def execute(self):
            self.attempts += 1
            if self.attempts == 1:
                self._pending = None
                raise redis.WatchError("concurrent writer")
            if self._pending and self._pending[0] != "__del__":
                self.set_calls.append(self._pending)
                self._value = self._pending[1]
            self._pending = None
            return [True]

    pipe = FlakyPipe()
    client = MagicMock()
    client.pipeline.return_value = pipe
    client.get.side_effect = lambda _key: pipe._value
    client.ttl.return_value = -1
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    assert store.delete({"role": "student", "erp_id": "202401001"}, "a") is True
    assert pipe.attempts == 2
    assert len(pipe.set_calls) == 1
    assert "Alpha." not in pipe.set_calls[0][1]
    assert "Beta." in pipe.set_calls[0][1]


def test_redis_delete_all_and_guest_noop():
    client = MagicMock()
    client.delete.return_value = 1
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    assert store.delete_all({"role": "student", "erp_id": "202401001"}) is True
    assert client.delete.call_count == 1
    assert store.delete({"role": "guest", "erp_id": "GUEST-1"}, "t1") is False
    assert store.delete_all({"role": "guest", "erp_id": "GUEST-1"}) is False
    # Guests never touch Redis.
    assert client.delete.call_count == 1
