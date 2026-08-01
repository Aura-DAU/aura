"""
Routing tests for the in-chat calendar-sync node (_n_personal_tools) added to
AuraChatGraph. The node is exercised in isolation on a stand-in `self` so these
stay fast and free of the full graph's heavy collaborators.

Guarantees:
  1. the keyword gate matches sync requests but not ordinary schedule lookups;
  2. the node surfaces a connect action for a student calendar-sync request;
  3. it never fires for non-student, non-PERSONAL_DATA, or non-calendar queries
     (the orchestrator is not even invoked), so the ERP path is untouched;
  4. a no-tool orchestrator run falls through instead of committing prose.
"""

import types

from pipeline.aura_chat_graph import (
    AuraChatGraph,
    SimpleIdentity,
    _is_calendar_sync_intent,
)


def test_keyword_gate_matches_sync_not_lookup():
    assert _is_calendar_sync_intent("add this to my schedule")
    assert _is_calendar_sync_intent("sync my timetable to google calendar")
    assert _is_calendar_sync_intent("add my classes to my calendar")
    assert not _is_calendar_sync_intent("what's my timetable today")
    assert not _is_calendar_sync_intent("what is my cgpa")


def _fake_self(run_return, counter=None):
    def run(**kwargs):
        if counter is not None:
            counter["n"] += 1
        return run_return
    return types.SimpleNamespace(ecampus_orchestrator=types.SimpleNamespace(run=run))


def _student_state(query, intent="PERSONAL_DATA", role="student"):
    return {
        "query": query,
        "identity": SimpleIdentity({"role": role, "erp_id": "S1"}),
        "ecampus_intent": intent,
        "history": [],
    }


def test_node_surfaces_connect_action():
    fake = _fake_self({
        "answer": "",
        "sources": [],
        "used_tools": True,
        "action_required": {
            "type": "connect_required",
            "provider": "google_calendar",
            "connect_path": "/settings/calendar",
            "message": "Connect your Google Calendar.",
        },
    })
    out = AuraChatGraph._n_personal_tools(fake, _student_state("add my timetable to my calendar"))
    result = out["result"]
    assert result["is_personal_data"] is True
    assert result["action_required"]["type"] == "connect_required"
    # No prose answer → the connect message becomes the bubble text.
    assert result["answer"] == "Connect your Google Calendar."


def test_node_skips_non_calendar_query_without_calling_orchestrator():
    counter = {"n": 0}
    fake = _fake_self({"used_tools": True, "answer": "x"}, counter)
    out = AuraChatGraph._n_personal_tools(fake, _student_state("what is my cgpa"))
    assert out.get("result") is None
    assert counter["n"] == 0


def test_node_skips_non_student():
    counter = {"n": 0}
    fake = _fake_self({"used_tools": True, "answer": "x"}, counter)
    out = AuraChatGraph._n_personal_tools(
        fake, _student_state("add to my calendar", role="faculty")
    )
    assert out.get("result") is None
    assert counter["n"] == 0


def test_node_falls_through_when_no_tool_used():
    fake = _fake_self({"answer": "I couldn't help.", "sources": [], "used_tools": False})
    out = AuraChatGraph._n_personal_tools(fake, _student_state("add this to my schedule"))
    assert out.get("result") is None
