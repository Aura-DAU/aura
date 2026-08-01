"""
Covers the in-chat "connect & authenticate" prompt wiring (the GPT/Claude
connector pattern) for Google Calendar:

  1. the narrow `personal_actions` tool scope exposes ONLY the student's own
     timetable + calendar MCP tools -- never the ecampus ERP read tools, so a
     calendar/schedule request routed here can't bypass the curated ERP path;
  2. when a calendar tool reports `calendar_not_connected`, the orchestrator
     surfaces a structured `action_required: connect_required` (not just prose);
  3. a normal tool run and a no-tool run set `used_tools` correctly and carry
     no connect action.

The LLM is stubbed; tool dispatch runs through the real in-process MCP server.
"""

import types

from pipeline.ecampus import orchestrator as orch_mod
from pipeline.ecampus.orchestrator import EcampusOrchestrator, _ECAMPUS_TOOL_REGISTRY
from pipeline.google_calendar import timetable_sync


class _FakeToolCall:
    def __init__(self, name, arguments="{}", call_id="call_1"):
        self.id = call_id
        self.type = "function"
        self.function = types.SimpleNamespace(name=name, arguments=arguments)


def _response(message):
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=message)])


def _msg(content=None, tool_calls=None):
    return types.SimpleNamespace(content=content, tool_calls=tool_calls)


def _orch_with_llm(monkeypatch, first_message, follow_up="Here's what I did."):
    orch = EcampusOrchestrator()
    calls = {"n": 0}

    def fake_call_llm(messages, tools=None, tool_choice=None):
        calls["n"] += 1
        return _response(first_message if calls["n"] == 1 else _msg(content=follow_up))

    monkeypatch.setattr(orch, "_call_llm", fake_call_llm)
    return orch


def test_personal_actions_scope_excludes_erp_read_tools():
    orch = EcampusOrchestrator()
    schemas = orch._tool_schemas("student", tool_scope="personal_actions")
    names = {s["function"]["name"] for s in schemas}
    assert "sync_timetable_to_calendar" in names
    # The ecampus ERP read tools must NOT be reachable on this scope.
    assert names.isdisjoint(set(_ECAMPUS_TOOL_REGISTRY.keys()))


def test_connect_required_surfaced_when_calendar_not_linked(monkeypatch):
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity, **k: {"status": "calendar_not_connected", "message": "Not linked."},
    )
    orch = _orch_with_llm(
        monkeypatch,
        _msg(content=None, tool_calls=[_FakeToolCall("sync_timetable_to_calendar")]),
    )
    result = orch.run(
        query="add my timetable to my google calendar",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    assert result["used_tools"] is True
    action = result["action_required"]
    assert action["type"] == "connect_required"
    assert action["provider"] == "google_calendar"
    assert action["connect_path"] == "/settings/calendar"


def test_successful_sync_carries_no_connect_action(monkeypatch):
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity, **k: {"status": "synced", "created": 5},
    )
    orch = _orch_with_llm(
        monkeypatch,
        _msg(content=None, tool_calls=[_FakeToolCall("sync_timetable_to_calendar")]),
    )
    result = orch.run(
        query="sync my timetable",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    assert result["used_tools"] is True
    assert "action_required" not in result


def test_no_tool_call_sets_used_tools_false(monkeypatch):
    orch = _orch_with_llm(monkeypatch, _msg(content="I can't do that.", tool_calls=None))
    result = orch.run(
        query="hello",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    assert result["used_tools"] is False
    assert "action_required" not in result
