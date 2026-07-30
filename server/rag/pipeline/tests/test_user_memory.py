from pipeline.memory.user_memory import (
    InMemoryUserMemoryStore,
    _identity_key,
)


def test_user_memory_merges_thread_summaries_for_signed_in_user():
    store = InMemoryUserMemoryStore()
    identity = {
        "role": "student",
        "email": "student@dau.ac.in",
        "erp_id": "202401001",
    }

    assert store.get(identity) == ""
    store.merge(identity, "User prefers concise answers.")
    store.merge(identity, "User is working on timetable questions.")

    memory = store.get(identity)
    assert "User prefers concise answers." in memory
    assert "User is working on timetable questions." in memory


def test_user_memory_ignores_guest_identity():
    store = InMemoryUserMemoryStore()
    guest = {"role": "guest", "erp_id": "GUEST-123"}

    assert _identity_key(guest) is None
    assert store.merge(guest, "Do not persist this.") == ""
    assert store.get(guest) == ""
