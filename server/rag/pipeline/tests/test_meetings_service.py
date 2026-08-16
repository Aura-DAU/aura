"""
Covers pipeline.google_calendar.meetings_service.get_my_meetings() — the
calendar-OWNER read path that backs the faculty (and student) dashboard's
merged "classes + meetings" schedule view. Distinct from slot_service.py
(tested elsewhere), which derives free/busy windows for someone ELSE's
calendar and never exposes event titles.
"""

import sys
from pathlib import Path
import datetime
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.google_calendar import meetings_service
from pipeline.google_calendar.token_vault import CalendarNotLinked

DATE = datetime.date(2026, 8, 17)


def test_unlinked_calendar_returns_empty_meetings_no_error():
    with patch("pipeline.google_calendar.meetings_service.is_linked", return_value=False):
        result = meetings_service.get_my_meetings("FAC_AG1", DATE)
    assert result["calendar_linked"] is False
    assert result["meetings"] == []
    assert "note" in result


def test_linked_calendar_returns_busy_events_only():
    events = [
        {"summary": "Dept meeting", "start": "2026-08-17T10:00:00+05:30", "end": "2026-08-17T11:00:00+05:30", "is_busy": True},
        {"summary": "Focus block", "start": "2026-08-17T14:00:00+05:30", "end": "2026-08-17T15:00:00+05:30", "is_busy": False},
    ]
    with patch("pipeline.google_calendar.meetings_service.is_linked", return_value=True), \
         patch("pipeline.google_calendar.meetings_service.get_events_on_date", return_value=events):
        result = meetings_service.get_my_meetings("FAC_AG1", DATE)
    assert result["calendar_linked"] is True
    assert len(result["meetings"]) == 1
    assert result["meetings"][0]["summary"] == "Dept meeting"


def test_expired_token_reports_unlinked_with_note():
    with patch("pipeline.google_calendar.meetings_service.is_linked", return_value=True), \
         patch("pipeline.google_calendar.meetings_service.get_events_on_date", side_effect=CalendarNotLinked()):
        result = meetings_service.get_my_meetings("FAC_AG1", DATE)
    assert result["calendar_linked"] is False
    assert result["meetings"] == []


def test_calendar_fetch_error_does_not_raise():
    with patch("pipeline.google_calendar.meetings_service.is_linked", return_value=True), \
         patch("pipeline.google_calendar.meetings_service.get_events_on_date", side_effect=RuntimeError("boom")):
        result = meetings_service.get_my_meetings("FAC_AG1", DATE)
    assert result["calendar_linked"] is True
    assert result["meetings"] == []
    assert "note" in result
