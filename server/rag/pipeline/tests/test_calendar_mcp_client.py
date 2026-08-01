"""
Covers the Google Calendar MCP client adapter
(pipeline/timetable/calendar_mcp_client.py) that exposes mcp_servers.gcal_server
to the agent orchestrator:
  1. all four calendar tools surface as student-only orchestrator Tools,
  2. erp_id is never present in a model-facing schema, and
  3. each handler injects erp_id from the verified identity -- ignoring any
     erp_id the model tried to supply -- and delegates to
     pipeline.google_calendar.timetable_sync.

Wiring only. The OAuth/write behaviour lives in timetable_sync and is covered
elsewhere. No network, no DB.
"""

from pipeline.google_calendar import timetable_sync
from pipeline.timetable import calendar_mcp_client as cmc

_CAL_TOOLS = {
    "calendar_status",
    "preview_timetable_sync",
    "sync_timetable_to_calendar",
    "unsync_timetable_from_calendar",
}


def test_all_four_tools_exposed_student_only():
    assert {t.name for t in cmc.calendar_mcp_tools_for_role("student")} == _CAL_TOOLS
    assert cmc.calendar_mcp_tools_for_role("faculty") == []


def test_erp_id_never_in_model_facing_schema():
    for t in cmc.calendar_mcp_tools():
        assert "erp_id" not in t.parameters.get("properties", {})
        assert "erp_id" not in t.parameters.get("required", [])


def test_sync_handler_injects_identity_erp_id(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity: seen.update(identity) or {"status": "synced", "created": 5},
    )
    result = cmc.calendar_mcp_registry()["sync_timetable_to_calendar"].handler(
        {"role": "student", "erp_id": "S1"}
    )
    assert result == {"status": "synced", "created": 5}
    assert seen == {"role": "student", "erp_id": "S1"}


def test_handler_ignores_model_supplied_erp_id(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity: seen.update(identity) or {"status": "synced"},
    )
    cmc.calendar_mcp_registry()["sync_timetable_to_calendar"].handler(
        {"role": "student", "erp_id": "REAL"}, erp_id="ATTACKER"
    )
    assert seen["erp_id"] == "REAL"


def test_preview_does_not_apply(monkeypatch):
    calls = []
    monkeypatch.setattr(
        timetable_sync, "preview",
        lambda identity: calls.append("preview") or {"status": "confirmation_required"},
    )
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity: calls.append("apply") or {"status": "synced"},
    )
    result = cmc.calendar_mcp_registry()["preview_timetable_sync"].handler(
        {"role": "student", "erp_id": "S1"}, request_context=None
    )
    assert result["status"] == "confirmation_required"
    assert calls == ["preview"]
