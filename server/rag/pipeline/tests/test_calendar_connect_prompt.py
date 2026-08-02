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
from pipeline.ecampus.orchestrator import (
    EcampusOrchestrator,
    _ECAMPUS_TOOL_REGISTRY,
    _required_calendar_tool,
    _is_calendar_unsync_intent,
    _is_timetable_edit_intent,
)
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


def _no_llm_orch(monkeypatch):
    """An orchestrator whose LLM call fails loudly. The deterministic calendar
    path runs the decided tool itself, so a supported calendar request must
    never reach the model -- that is exactly what keeps it working when a
    self-hosted model won't emit a forced tool call."""
    orch = EcampusOrchestrator()

    def _boom(*_a, **_k):
        raise AssertionError("deterministic calendar path must not call the LLM")

    monkeypatch.setattr(orch, "_call_llm", _boom)
    return orch


def test_connect_required_surfaced_when_calendar_not_linked(monkeypatch):
    # With no linked calendar, the direct sync reports calendar_not_connected →
    # a structured connect CTA, with no LLM or request for timetable details.
    monkeypatch.setattr(
        timetable_sync, "preview",
        lambda identity, **k: {"status": "calendar_not_connected", "message": "Not linked."},
    )
    orch = _no_llm_orch(monkeypatch)
    result = orch.run(
        query="add my timetable to my google calendar",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    print("DEBUG: result =", result)
    assert result["used_tools"] is True
    action = result["action_required"]
    assert action["type"] == "connect_required"
    assert action["provider"] == "google_calendar"
    assert action["connect_path"] == "/settings/calendar"


def test_sync_request_runs_sync_deterministically(monkeypatch):
    # An explicit sync request authorizes the idempotent write. The effective
    # timetable service resolves section/electives without another user turn.
    seen = {}

    def _apply(identity, **kwargs):
        seen.update({"identity": identity, **kwargs})
        return {
            "status": "synced",
            "created": 20,
            "updated": 0,
            "removed": 0,
        }

    monkeypatch.setattr(timetable_sync, "apply", _apply)
    orch = _no_llm_orch(monkeypatch)
    result = orch.run(
        query="can you sync my google calendar",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    assert seen == {
        "identity": {"role": "student", "erp_id": "S1"},
        "async_mode": False,
    }
    assert result["used_tools"] is True
    assert "action_required" not in result
    assert "Google Calendar" in result["answer"]
    assert "20 created" in result["answer"]


def test_confirmation_runs_the_sync_and_carries_no_connect_action(monkeypatch):
    # "yes" right after a calendar preview runs the write tool deterministically.
    called = {}

    def _apply(identity, **k):
        called.update({"synced": True, **k})
        return {"status": "queued", "message": "Sync started in the background."}

    monkeypatch.setattr(timetable_sync, "apply", _apply)
    orch = _no_llm_orch(monkeypatch)
    result = orch.run(
        query="yes",
        identity={"role": "student", "erp_id": "S1"},
        history=[{
            "role": "assistant",
            "content": "This will create 20 events on your Google Calendar. Confirm to proceed.",
        }],
        tool_scope="personal_actions",
    )
    assert called.get("synced") is True
    assert called["async_mode"] is False
    assert result["used_tools"] is True
    assert "action_required" not in result


def test_no_tool_call_sets_used_tools_false(monkeypatch):
    # A non-calendar query has no decided tool, so it falls to the model path;
    # a model that emits no tool call yields used_tools False (curated fallback).
    orch = _orch_with_llm(monkeypatch, _msg(content="I can't do that.", tool_calls=None))
    result = orch.run(
        query="hello",
        identity={"role": "student", "erp_id": "S1"},
        tool_scope="personal_actions",
    )
    assert result["used_tools"] is False
    assert "action_required" not in result


def test_confirmation_requires_sync_tool_only_after_calendar_preview():
    preview_history = [{
        "role": "assistant",
        "content": "This will create 20 events on Google Calendar. Confirm to proceed.",
    }]

    assert _required_calendar_tool("yes", preview_history) == "sync_timetable_to_calendar"
    assert _required_calendar_tool("yes", []) is None


def test_explicit_sync_request_needs_no_separate_confirmation():
    assert _required_calendar_tool("sync my time table", []) == "sync_timetable_to_calendar"
    assert _required_calendar_tool(
        "sync my Google Calendar", []
    ) == "sync_timetable_to_calendar"


def test_timetable_details_follow_up_resumes_sync_without_manual_input():
    history = [{
        "role": "assistant",
        "content": (
            "To sync your timetable, I need your section and elective details."
        ),
    }]

    assert _required_calendar_tool(
        "fetch them from my timetable", history
    ) == "sync_timetable_to_calendar"


def test_academic_calendar_lookup_does_not_select_personal_calendar_tool():
    assert _required_calendar_tool("When is the academic calendar deadline?", []) is None


def test_timetable_edits_do_not_select_calendar_tools():
    edit_requests = [
        "move my Monday lecture to 3 PM",
        "add a lab on Friday to my timetable",
        "remove my Tuesday class",
    ]

    for request in edit_requests:
        assert _is_timetable_edit_intent(request)
        assert not _is_calendar_unsync_intent(request)
        assert _required_calendar_tool(request, []) is None


def test_unsync_intent_detected_but_not_dispatched_without_confirmation():
    # A removal is a write: it is recognised, but never dispatched directly, so
    # nothing is deleted until the student confirms.
    assert _is_calendar_unsync_intent("remove my timetable from my google calendar")
    assert _is_calendar_unsync_intent("delete my classes from the calendar")
    assert _required_calendar_tool("remove my timetable from my calendar", []) is None
    # An ordinary sync request is not mistaken for a removal.
    assert not _is_calendar_unsync_intent("add my timetable to my calendar")


def test_unsync_confirmation_runs_unsync_tool(monkeypatch):
    # "yes" right after a removal prompt runs unsync deterministically -- and is
    # never mistaken for a sync (whose confirmation context the prompt also
    # matches). No LLM involved.
    called = {}

    def _unsync(identity, **k):
        called["unsynced"] = True
        return {"status": "unsynced", "removed": 7, "events_kept": False}

    monkeypatch.setattr(timetable_sync, "unsync", _unsync)
    orch = _no_llm_orch(monkeypatch)
    result = orch.run(
        query="yes",
        identity={"role": "student", "erp_id": "S1"},
        history=[{
            "role": "assistant",
            "content": (
                "This will remove the timetable events AURA added to your "
                "Google Calendar. Confirm to proceed and I'll clear them."
            ),
        }],
        tool_scope="personal_actions",
    )
    assert called.get("unsynced") is True
    assert result["used_tools"] is True
    assert "7" in result["answer"]


def test_confirmation_after_sync_preview_never_triggers_unsync(monkeypatch):
    # Guard the disambiguation: a "yes" after an *add* preview must sync, not
    # unsync, even though both confirmation contexts mention Google Calendar.
    monkeypatch.setattr(
        timetable_sync, "unsync",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not unsync")),
    )
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity, **k: {"status": "queued", "message": "Sync started."},
    )
    orch = _no_llm_orch(monkeypatch)
    result = orch.run(
        query="yes",
        identity={"role": "student", "erp_id": "S1"},
        history=[{
            "role": "assistant",
            "content": (
                "This will create or update 20 recurring weekly events on your "
                "Google Calendar. Confirm to proceed."
            ),
        }],
        tool_scope="personal_actions",
    )
    assert result["used_tools"] is True
