"""
Covers the confirm-before-write gate on sync_timetable_to_google_calendar
(same pattern as update_my_timetable) and that it's restricted to students
only — faculty never hold the calendar.events write scope (they only ever
get calendar.readonly, see calendar_routes.py's /connect), and
timetable_sync.apply()/preview() call the student-only
service.get_effective_timetable, so allowing faculty here would just be a
tool that always fails for them.
"""

from pipeline.timetable import tool_registry
from pipeline.google_calendar import timetable_sync


def student(erp_id="S1"):
    return {"role": "student", "erp_id": erp_id, "current_year": 3, "current_sem": 5, "current_sec": "A"}


def test_tool_is_registered_write_category_student_only():
    tool = tool_registry.TOOL_REGISTRY["sync_timetable_to_google_calendar"]
    assert tool.category == "write"
    assert tool.allowed_roles == ["student"]
    assert "faculty" not in tool.allowed_roles


def test_first_call_without_confirm_returns_preview_not_apply(monkeypatch):
    calls = []
    monkeypatch.setattr(timetable_sync, "preview", lambda identity: calls.append(("preview", identity)) or {"status": "confirmation_required"})
    monkeypatch.setattr(timetable_sync, "apply", lambda identity: calls.append(("apply", identity)) or {"status": "synced"})

    result = tool_registry._handle_sync_timetable_to_google_calendar(student(), confirm=False)

    assert result["status"] == "confirmation_required"
    assert calls == [("preview", student())]


def test_confirmed_call_applies_the_sync(monkeypatch):
    calls = []
    monkeypatch.setattr(timetable_sync, "preview", lambda identity: calls.append(("preview", identity)) or {"status": "confirmation_required"})
    monkeypatch.setattr(timetable_sync, "apply", lambda identity: calls.append(("apply", identity)) or {"status": "synced", "created": 5})

    result = tool_registry._handle_sync_timetable_to_google_calendar(student(), confirm=True)

    assert result == {"status": "synced", "created": 5}
    assert calls == [("apply", student())]
