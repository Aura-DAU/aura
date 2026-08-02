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


def test_short_conversation_is_captured_from_questions():
    # A chat that never compacts (no thread summary) must STILL leave a durable
    # trace — the user's actual questions — so it is remembered in later threads.
    capture = chat_routes._conversation_capture(
        thread_summary="",
        history=[
            {"role": "user", "content": "What is the hostel fee?"},
            {"role": "assistant", "content": "..."},
        ],
        question="And the mess fee?",
    )
    assert "What is the hostel fee?" in capture
    assert "And the mess fee?" in capture


def test_capture_prefers_thread_digest_when_present():
    capture = chat_routes._conversation_capture(
        thread_summary="## Profile\nB.Tech ICT student comparing electives.",
        history=[{"role": "user", "content": "Which one clashes least?"}],
        question="Which one clashes least?",
    )
    assert "comparing electives" in capture
    assert "Latest question: Which one clashes least?" in capture


def test_capture_empty_when_nothing_to_record():
    assert chat_routes._conversation_capture("", [], "") == ""
