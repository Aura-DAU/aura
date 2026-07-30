import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.routes import chat_routes


class _FakeConversationMemory:
    summary_max_tokens = 1


def test_persistent_memory_has_dedicated_generation_budget(monkeypatch):
    monkeypatch.setenv("AURA_USER_MEMORY_TOKENS", "1")
    monkeypatch.setattr(chat_routes, "get_conversation_memory", _FakeConversationMemory)

    summary = chat_routes._summary_for_generation(
        "User prefers short direct answers and timetable examples.",
        "Current thread summary that already fills the thread budget.",
    )

    assert "Persistent User Memory" in summary
    assert "User" in summary
    assert "Current Thread Summary" in summary
