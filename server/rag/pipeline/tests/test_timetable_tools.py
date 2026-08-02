"""
Covers the core safety invariant of pipeline.timetable: a student can only
ever read or write THEIR OWN timetable, never another student's — and that
master-timetable rows are merged correctly with per-student overrides.
"""

import uuid
import pytest

from pipeline.timetable import service, tool_registry


class FakeDB:
    """In-memory stand-in for db.connection, scoped to one test."""

    def __init__(self):
        self.identity_map = {}       # erp_id -> row
        self.master = []             # list of dict rows
        self.overrides = []          # list of dict rows

    # -- query/execute dispatch, matched loosely on SQL shape --------------
    def query(self, sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM timetable_master" in sql_norm:
            if len(params) == 2:
                year, sem = params
                return [r for r in self.master if r["year"] == year and r["sem"] == sem and (r["sec"] is None or r["sec"] == "" or r["sec"] == "A")]
            year, sem, sec = params
            return [r for r in self.master if r["year"] == year and r["sem"] == sem and r["sec"] == sec]
        if "FROM timetable_overrides" in sql_norm:
            erp_id = params[0]
            return [r for r in self.overrides if r["erp_id"] == erp_id and r["is_active"]]
        if "FROM user_identity_map" in sql_norm:
            erp_id = params[0]
            row = self.identity_map.get(erp_id)
            return [row] if row else []
        if "FROM student_elective_selections" in sql_norm:
            # No test in this file exercises the elective-selection feature
            # itself (see test_elective_and_cohort_scoping.py for that) —
            # zero selections is service.py's documented default, meaning
            # every elective is shown unfiltered.
            return []
        raise AssertionError(f"Unexpected query: {sql_norm}")

    def execute(self, sql, params=()):
        sql_norm = " ".join(sql.split())
        if "INSERT INTO timetable_overrides" in sql_norm:
            (erp_id, kind, master_id, day_of_week, start_time, end_time,
             course_code, course_name, session_type, room, faculty_name, note) = params
            self.overrides.append(dict(
                id=str(uuid.uuid4()), erp_id=erp_id, kind=kind, master_id=master_id,
                day_of_week=day_of_week, start_time=start_time, end_time=end_time,
                course_code=course_code, course_name=course_name, session_type=session_type,
                room=room, faculty_name=faculty_name, note=note, is_active=True,
            ))
        elif "UPDATE timetable_overrides" in sql_norm:
            override_id, erp_id = params
            for r in self.overrides:
                if r["id"] == override_id and r["erp_id"] == erp_id:
                    r["is_active"] = False
        else:
            raise AssertionError(f"Unexpected execute: {sql_norm}")


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(service, "db_conn", db)
    return db


def student(erp_id="S1", year=3, sem=5, sec="A"):
    return {"role": "student", "erp_id": erp_id, "current_year": year, "current_sem": sem, "current_sec": sec}


def _master_row(**overrides):
    row = dict(
        id=str(uuid.uuid4()), year=3, sem=5, sec="A", day_of_week=1,
        start_time="17:00", end_time="18:30", course_code="IT302",
        course_name="Computer Networks", session_type="lecture",
        room="Room 102", faculty_name="Dr. X",
    )
    row.update(overrides)
    return row


def test_effective_timetable_returns_master_when_no_overrides(fake_db):
    fake_db.master.append(_master_row())
    result = service.get_effective_timetable(student())
    assert len(result["timetable"]) == 1
    assert result["timetable"][0]["course_code"] == "IT302"
    assert result["timetable"][0]["is_custom"] is False


def test_apply_change_replace_only_affects_requesting_student(fake_db):
    master_row = _master_row()
    fake_db.master.append(master_row)

    service.apply_change(
        student("S1"), kind="replace", day="Tuesday", start_time="17:00",
        course_code="IT302", room="Room 999",
    )

    # S1 sees the change...
    s1_view = service.get_effective_timetable(student("S1"))
    assert s1_view["timetable"][0]["room"] == "Room 999"
    assert s1_view["timetable"][0]["is_custom"] is True

    # ...but S2, same cohort, does not.
    s2_view = service.get_effective_timetable(student("S2"))
    assert s2_view["timetable"][0]["room"] == "Room 102"
    assert s2_view["timetable"][0]["is_custom"] is False


def test_agent_timetable_change_accepts_orchestrator_context(fake_db, monkeypatch):
    fake_db.master.append(_master_row())
    monkeypatch.setattr(
        tool_registry.timetable_sync,
        "resync_if_linked",
        lambda identity: {"status": "not_linked"},
    )

    result = tool_registry._handle_update_my_timetable(
        student("S1"),
        kind="replace",
        day="Tuesday",
        start_time="17:00",
        course_code="IT302",
        room="Room 999",
        confirm=True,
        request_context=object(),
    )

    assert result["status"] == "applied"
    assert result["timetable"][0]["room"] == "Room 999"
    assert result["calendar_sync"]["status"] == "not_linked"


def test_clear_change_cannot_touch_another_students_override(fake_db):
    fake_db.master.append(_master_row())
    service.apply_change(student("S1"), kind="replace", day="Tuesday", start_time="17:00",
                          course_code="IT302", room="Room 999")
    override_id = fake_db.overrides[0]["id"]

    # S2 attempting to clear S1's override should be a no-op (scoped by erp_id in SQL).
    service.clear_change(student("S2"), override_id)
    assert fake_db.overrides[0]["is_active"] is True

    # S1 clearing their own override works.
    service.clear_change(student("S1"), override_id)
    assert fake_db.overrides[0]["is_active"] is False


def test_add_new_slot_is_marked_custom_and_scoped(fake_db):
    service.apply_change(
        student("S1"), kind="add", day="Friday", start_time="16:00", end_time="17:00",
        course_name="Extra Doubt Session", session_type="tutorial",
    )
    s1_view = service.get_effective_timetable(student("S1"))
    assert len(s1_view["timetable"]) == 1
    assert s1_view["timetable"][0]["is_custom"] is True

    s2_view = service.get_effective_timetable(student("S2"))
    assert s2_view["timetable"] == []


def test_non_student_role_is_rejected(fake_db):
    with pytest.raises(service.TimetableError):
        service.get_effective_timetable({"role": "faculty", "erp_id": "F1"})


def test_missing_cohort_fallback_to_common(fake_db):
    res = service.get_effective_timetable({"role": "student", "erp_id": "S3", "current_year": None,
                                          "current_sem": None, "current_sec": None})
    assert res["is_common"] is True
    assert res["needs_configuration"] is True
