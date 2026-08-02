import pytest
from pipeline.timetable import service

def student(erp_id="S1", year=None, sem=None, sec=None):
    return {"role": "student", "erp_id": erp_id, "current_year": year, "current_sem": sem, "current_sec": sec}

# Test data representing timetable master rows
COHORT_A_ROW = {
    "id": 1, "year": 1, "sem": 1, "sec": "A", "day_of_week": 0,
    "start_time": "09:00", "end_time": "10:00", "course_code": "IT201",
    "course_name": "Database Systems", "session_type": "lecture", "room": "CEP-103",
    "faculty_name": "PD", "course_type": "Core"
}
COHORT_COMMON_ROW = {
    "id": 2, "year": 1, "sem": 1, "sec": None, "day_of_week": 1,
    "start_time": "10:00", "end_time": "11:00", "course_code": "PC1 (ICT)",
    "course_name": "Program Core", "session_type": "lecture", "room": "CEP-106",
    "faculty_name": "RM", "course_type": "Core"
}
COHORT_OTHER_ROW = {
    "id": 3, "year": 3, "sem": 5, "sec": "B", "day_of_week": 2,
    "start_time": "11:00", "end_time": "12:00", "course_code": "IT301",
    "course_name": "Software Engineering", "session_type": "lecture", "room": "CEP-108",
    "faculty_name": "ST", "course_type": "Core"
}

ALL_MASTER_ROWS = [COHORT_A_ROW, COHORT_COMMON_ROW, COHORT_OTHER_ROW]

def _fake_db_query(sql, params=()):
    sql_upper = sql.upper()
    if "USER_IDENTITY_MAP" in sql_upper:
        # Simulate student S1 has no cohort set, S2 has cohort set
        if len(params) > 0 and params[0] == "S2":
            return [{"current_year": 2, "current_sem": 3, "current_sec": "A", "email": "s2@dau.ac.in", "role": "student"}]
        return [{"current_year": None, "current_sem": None, "current_sec": None, "email": "s1@dau.ac.in", "role": "student"}]
    if "TIMETABLE_MASTER" in sql_upper:
        # If filtering by year, sem, sec
        if "SEC = %S" in sql_upper or "SEC IS NULL" in sql_upper:
            # We want to filter ALL_MASTER_ROWS
            year, sem = params[0], params[1]
            if len(params) > 2:
                sec = params[2]
                return [r for r in ALL_MASTER_ROWS if r["year"] == year and r["sem"] == sem and (r["sec"] == sec or r["sec"] is None)]
            else:
                return [r for r in ALL_MASTER_ROWS if r["year"] == year and r["sem"] == sem and (r["sec"] is None or r["sec"] == "A")]
        # Distinct query
        return [
            {"program": "BTech", "year": 2, "sem": 3, "sec": "A"},
            {"program": "BTech", "year": 2, "sem": 3, "sec": "B"},
            {"program": "BTech", "year": 3, "sem": 5, "sec": "B"}
        ]
    if "STUDENT_ELECTIVE_SELECTIONS" in sql_upper:
        return []
    if "TIMETABLE_OVERRIDES" in sql_upper:
        return []
    return []

def test_get_effective_timetable_fallback_to_common(monkeypatch):
    monkeypatch.setattr(service.db_conn, "query", _fake_db_query)
    
    # S1 has no cohort set (first time)
    identity_s1 = student("S1", None, None, None)
    res = service.get_effective_timetable(identity_s1)
    
    assert res["is_common"] is True
    assert res["needs_configuration"] is True
    # Should include COHORT_COMMON_ROW and COHORT_A_ROW (default fallback)
    timetable_ids = [slot["id"] for slot in res["timetable"]]
    assert "2" in timetable_ids  # Common row
    assert "1" in timetable_ids  # Section A row (representative fallback)

def test_get_effective_timetable_configured_student(monkeypatch):
    monkeypatch.setattr(service.db_conn, "query", _fake_db_query)
    
    # S2 has cohort set
    identity_s2 = student("S2", 2, 3, "A")
    res = service.get_effective_timetable(identity_s2)
    
    assert res["is_common"] is False
    assert res["needs_configuration"] is True  # True because electives are not configured yet
