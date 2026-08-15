"""
Covers pipeline.timetable.service.get_faculty_timetable() and its
_resolve_faculty_initials() fallback chain:
  1. identity.faculty_initials, if the caller's JWT already carries it
     (the REST /timetable/me path — see api/routes/timetable_routes.py)
  2. user_identity_map.faculty_initials, if cached in the DB
  3. re-inferred from FACULTY_INITIALS via _infer_role_and_cohort(email)

(2) and (3) exist because the chat/agent path's internal JWT is
deliberately kept minimal (role/erp_id/department/email only — see
aura/app/api/chat/route.ts) and doesn't carry faculty_initials directly.
"""

import pytest

from pipeline.timetable import service


class FakeDB:
    """In-memory stand-in for db.connection, scoped to one test."""

    def __init__(self):
        self.identity_map = {}   # erp_id -> row
        self.master = []         # list of dict rows (timetable_master)

    def query(self, sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM timetable_master" in sql_norm:
            needle = params[0].upper()
            return [r for r in self.master if r["faculty_name"].upper() == needle]
        if "FROM user_identity_map" in sql_norm:
            erp_id = params[0]
            row = self.identity_map.get(erp_id)
            return [row] if row else []
        raise AssertionError(f"Unexpected query: {sql_norm}")

    def execute(self, sql, params=()):
        raise AssertionError(f"Unexpected execute: {sql}")


@pytest.fixture
def fake_db(monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(service, "db_conn", db)
    return db


def _master_row(faculty_name="AG1", **overrides):
    row = dict(
        id="row-1", year=3, sem=5, sec="A", day_of_week=1,
        start_time="17:00", end_time="18:30", course_code="IT302",
        course_name="Computer Networks", session_type="lecture",
        room="CEP-209", faculty_name=faculty_name,
        batch_raw="", branch="ICT", program="BTech", credits=3, course_type="core",
    )
    row.update(overrides)
    return row


def faculty(erp_id="FAC_ABHISHEK.GUPTA", email=None, faculty_initials=None):
    return {"role": "faculty", "erp_id": erp_id, "email": email, "faculty_initials": faculty_initials}


def test_get_faculty_timetable_uses_initials_already_on_identity(fake_db):
    fake_db.master.append(_master_row(faculty_name="AG1"))
    result = service.get_faculty_timetable(faculty(faculty_initials="AG1"))
    assert result["faculty"] == "AG1"
    assert result["total_classes_per_week"] == 1
    assert result["timetable"][0]["course_code"] == "IT302"


def test_get_faculty_timetable_falls_back_to_db_cached_initials(fake_db):
    # Simulates the chat/agent path: identity carries no faculty_initials,
    # but user_identity_map already has it cached from a prior REST login.
    fake_db.master.append(_master_row(faculty_name="AG1"))
    fake_db.identity_map["FAC_ABHISHEK.GUPTA"] = {"faculty_initials": "AG1", "email": "abhishek.gupta@dau.ac.in"}
    result = service.get_faculty_timetable(faculty(faculty_initials=None))
    assert result["faculty"] == "AG1"
    assert result["total_classes_per_week"] == 1


def test_get_faculty_timetable_falls_back_to_reinference_from_email(fake_db):
    # Neither identity nor the DB row has faculty_initials cached yet --
    # re-derive it from FACULTY_INITIALS the same way login does.
    fake_db.master.append(_master_row(faculty_name="AG1"))
    fake_db.identity_map["FAC_ABHISHEK.GUPTA"] = {"faculty_initials": None, "email": None}
    result = service.get_faculty_timetable(
        faculty(faculty_initials=None, email="abhishek.gupta@dau.ac.in")
    )
    assert result["faculty"] == "AG1"
    assert result["total_classes_per_week"] == 1


def test_get_faculty_timetable_unresolvable_initials_returns_no_classes(fake_db):
    # A faculty member with no resolvable initials anywhere falls back to
    # matching on their raw erp_id (e.g. "FAC_UNKNOWN") -- which never
    # appears in timetable_master.faculty_name, so this safely comes back
    # as an empty schedule rather than raising or showing anyone else's.
    fake_db.master.append(_master_row(faculty_name="AG1"))
    result = service.get_faculty_timetable(faculty(erp_id="FAC_UNKNOWN", email="unknown@dau.ac.in"))
    assert result["total_classes_per_week"] == 0
    assert result["timetable"] == []


def test_get_faculty_timetable_rejects_student_role(fake_db):
    with pytest.raises(service.TimetableForbiddenError):
        service.get_faculty_timetable({"role": "student", "erp_id": "202301234"})
