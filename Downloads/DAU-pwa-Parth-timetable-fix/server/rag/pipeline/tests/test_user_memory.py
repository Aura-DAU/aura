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
    with patch("redis.Redis.from_url", return_value=client):
        store = RedisUserMemoryStore("redis://localhost:6379/0")

    store.merge({"role": "student", "erp_id": "202401001"}, "summary")

    assert pipe.set_calls
    assert pipe.set_calls[0][2] == DEFAULT_USER_MEMORY_TTL_SECONDS
