"""
Covers the Google Calendar MCP server (mcp_servers/gcal_server.py):
  1. the four calendar tools are registered on the MCP server, and
  2. each tool delegates to the existing pipeline.google_calendar.timetable_sync
     with a minimal student identity built from the erp_id argument.

These assert the wiring only — the actual OAuth/write behaviour lives in
timetable_sync/writer/token_vault and is covered elsewhere. No network, no DB.
"""

import asyncio

from mcp_servers import gcal_server
from pipeline.google_calendar import timetable_sync


def _tool_names() -> set[str]:
    tools = asyncio.run(gcal_server.mcp.list_tools())
    return {t.name for t in tools}


def test_all_four_calendar_tools_registered():
    assert {
        "calendar_status",
        "preview_timetable_sync",
        "sync_timetable_to_calendar",
        "unsync_timetable_from_calendar",
    } <= _tool_names()


def test_sync_delegates_to_timetable_sync_apply_with_identity(monkeypatch):
    seen = {}
    monkeypatch.setattr(
        timetable_sync, "apply",
        lambda identity, **kwargs: (
            seen.update({"identity": identity, **kwargs})
            or {"status": "synced", "created": 5}
        ),
    )
    result = gcal_server.sync_timetable_to_calendar("S1")
    assert result == {"status": "synced", "created": 5}
    assert seen == {
        "identity": {"role": "student", "erp_id": "S1"},
        "async_mode": False,
    }


def test_preview_does_not_call_apply(monkeypatch):
    calls = []
    monkeypatch.setattr(timetable_sync, "preview", lambda identity: calls.append(("preview", identity)) or {"status": "confirmation_required"})
    monkeypatch.setattr(timetable_sync, "apply", lambda identity: calls.append(("apply", identity)) or {"status": "synced"})

    result = gcal_server.preview_timetable_sync("S1")

    assert result["status"] == "confirmation_required"
    assert calls == [("preview", {"role": "student", "erp_id": "S1"})]


def test_status_and_unsync_delegate(monkeypatch):
    monkeypatch.setattr(timetable_sync, "status", lambda identity: {"calendar_linked": True, "_id": identity["erp_id"]})
    monkeypatch.setattr(timetable_sync, "unsync", lambda identity: {"status": "unsynced", "removed": 3, "_id": identity["erp_id"]})

    assert gcal_server.calendar_status("S9") == {"calendar_linked": True, "_id": "S9"}
    assert gcal_server.unsync_timetable_from_calendar("S9") == {"status": "unsynced", "removed": 3, "_id": "S9"}
