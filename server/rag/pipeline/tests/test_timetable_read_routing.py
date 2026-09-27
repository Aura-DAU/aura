"""
Routing tests for the timetable read node (_n_timetable_read) and the
eCampus-free personal-data node.

Guarantees:
  1. only own-timetable and named-cohort timetable questions reach the agent;
     clubs, faculty, fees and policies go to grounded RAG;
  2. an agent reply that used no tool is never shown to the user;
  3. a cohort lookup whose tool failed falls through to RAG;
  4. without an ERP connection, a PERSONAL records question gets a clear
     "unavailable" answer instead of a generated one.
"""

import types

from access_control import AccessDecision
from pipeline.aura_chat_graph import (
    PERSONAL_RECORDS_UNAVAILABLE_RESPONSE,
    AuraChatGraph,
    SimpleIdentity,
)
from pipeline.timetable.agent import (
    SCOPE_PERSONAL,
    SCOPE_PUBLIC_TIMETABLE,
    TimetableAgent,
    is_cohort_timetable_query,
    is_own_timetable_query,
)


def _fake_self(run_return, calls):
    def run(**kwargs):
        calls.append(kwargs)
        return run_return

    return types.SimpleNamespace(
        timetable_agent=types.SimpleNamespace(run=run),
        _tool_role=AuraChatGraph._tool_role,
    )


def _state(query, role="student"):
    return {
        "query": query,
        "identity": SimpleIdentity({"role": role, "erp_id": "S1"}),
        "history": [],
    }


def test_timetable_patterns():
    assert is_own_timetable_query("what is my time table?")
    assert is_own_timetable_query("do I have labs tomorrow")
    assert not is_own_timetable_query("my timetable for ICT 1st year")
    assert is_cohort_timetable_query("timetable for btech ict sem 3 section A")
    assert is_cohort_timetable_query("my timetable for ICT 1st year")
    assert not is_cohort_timetable_query("exam schedule for ICT")
    assert not is_cohort_timetable_query("what is the fee for btech ict")


def test_own_timetable_routes_to_personal_scope():
    calls = []
    fake = _fake_self({"used_tools": True, "tool_succeeded": True, "answer": "Mon 9:00 IT205"}, calls)
    out = AuraChatGraph._n_timetable_read(fake, _state("what is my timetable"))
    assert out["result"]["answer"] == "Mon 9:00 IT205"
    assert out["result"]["is_personal_data"] is True
    assert calls[0]["tool_scope"] == SCOPE_PERSONAL


def test_cohort_timetable_routes_to_public_scope():
    calls = []
    fake = _fake_self({"used_tools": True, "tool_succeeded": True, "answer": "Tue 10:00 IT301"}, calls)
    out = AuraChatGraph._n_timetable_read(
        fake, _state("timetable for btech ict sem 3 section A", role="faculty")
    )
    assert out["result"]["answer"] == "Tue 10:00 IT301"
    assert out["result"]["is_personal_data"] is False
    assert calls[0]["tool_scope"] == SCOPE_PUBLIC_TIMETABLE


def test_general_questions_never_reach_the_agent():
    calls = []
    fake = _fake_self({"used_tools": True, "answer": "x"}, calls)
    for query in (
        "who is the convener of the programming club",
        "who is Aditya Tatu",
        "what is the fee for btech ict",
        "what is the anti-ragging policy",
        "what is my cgpa",
    ):
        out = AuraChatGraph._n_timetable_read(fake, _state(query))
        assert out.get("result") is None, query
    assert calls == []


def test_guest_never_reaches_the_agent():
    calls = []
    fake = _fake_self({"used_tools": True, "answer": "x"}, calls)
    out = AuraChatGraph._n_timetable_read(fake, _state("what is my timetable", role="guest"))
    assert out.get("result") is None
    assert calls == []


def test_answer_without_tool_call_is_discarded():
    calls = []
    fake = _fake_self({"used_tools": False, "answer": "You have IT205 on Monday."}, calls)
    out = AuraChatGraph._n_timetable_read(fake, _state("what is my timetable"))
    assert out.get("result") is None


def test_failed_cohort_lookup_falls_through_to_rag():
    calls = []
    fake = _fake_self(
        {"used_tools": True, "tool_succeeded": False, "answer": "Not available."}, calls
    )
    out = AuraChatGraph._n_timetable_read(fake, _state("schedule for 2nd year MnC section B"))
    assert out.get("result") is None


def test_agent_reports_no_tool_run(monkeypatch):
    agent = TimetableAgent()
    message = types.SimpleNamespace(content="You have IT205 on Monday.", tool_calls=None)
    response = types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])
    monkeypatch.setattr(agent, "_call_llm", lambda *a, **k: response)
    result = agent.run(
        query="what is my timetable",
        identity={"erp_id": "S1", "role": "student"},
        tool_scope=SCOPE_PERSONAL,
    )
    assert result["used_tools"] is False


def test_public_scope_only_exposes_cohort_lookup():
    names = {
        s["function"]["name"]
        for s in TimetableAgent()._tool_schemas("student", tool_scope=SCOPE_PUBLIC_TIMETABLE)
    }
    assert names == {"get_cohort_timetable"}


def _personal_data_self(available):
    return types.SimpleNamespace(
        _resolve_target=lambda target, identity: identity.erp_id,
        access_gate=types.SimpleNamespace(
            evaluate=lambda **kwargs: types.SimpleNamespace(
                decision=AccessDecision.ALLOWED,
                reason=None,
                scope_context=None,
                course_codes=[],
            )
        ),
        audit_log=types.SimpleNamespace(record=lambda **kwargs: None),
        erp_connector=types.SimpleNamespace(available=available),
    )


def _personal_state(query_type):
    state = _state("what is my cgpa")
    state["query_type"] = query_type
    state["classification"] = {"target": "self", "erp_fields": ["cgpa"]}
    return state


def test_personal_records_unavailable_without_erp():
    out = AuraChatGraph._n_personal_data(_personal_data_self(False), _personal_state("PERSONAL"))
    assert out["result"]["answer"] == PERSONAL_RECORDS_UNAVAILABLE_RESPONSE
    assert out["result"]["sources"] == []


def test_mixed_query_keeps_public_half_without_erp():
    out = AuraChatGraph._n_personal_data(_personal_data_self(False), _personal_state("MIXED"))
    assert out.get("result") is None
    assert out["erp_context"] == ""
