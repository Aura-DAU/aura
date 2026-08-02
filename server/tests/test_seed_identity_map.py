import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_DIR))

from db import seed_identity_map


def _student() -> dict:
    return {
        "erp_id": "202401001",
        "email": "student@dau.ac.in",
        "role": "student",
        "dept": "ICT",
    }


def test_sync_academic_scope_backfills_missing_student(monkeypatch):
    monkeypatch.setattr(seed_identity_map.db_conn, "query", lambda *_: [])
    calls = []
    monkeypatch.setattr(
        seed_identity_map,
        "upsert_student_academic_scope",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    assert seed_identity_map.sync_academic_scope(_student(), dry_run=False) == "SYNC"
    assert calls == [{"erp_id": "202401001", "dept": "ICT"}]


def test_sync_academic_scope_skips_complete_student(monkeypatch):
    monkeypatch.setattr(
        seed_identity_map.db_conn,
        "query",
        lambda *_: [{
            "department_id": "ICT",
            "derivation_rule_version": seed_identity_map.DERIVATION_RULE_VERSION,
            "profile_erp_id": "202401001",
        }],
    )
    calls = []
    monkeypatch.setattr(
        seed_identity_map,
        "upsert_student_academic_scope",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    assert seed_identity_map.sync_academic_scope(_student(), dry_run=False) == "NOOP"
    assert calls == []


def test_sync_academic_scope_dry_run_does_not_write(monkeypatch):
    monkeypatch.setattr(seed_identity_map.db_conn, "query", lambda *_: [])
    calls = []
    monkeypatch.setattr(
        seed_identity_map,
        "upsert_student_academic_scope",
        lambda **kwargs: calls.append(kwargs) or True,
    )

    assert seed_identity_map.sync_academic_scope(_student(), dry_run=True) == "SYNC"
    assert calls == []


def test_sync_academic_scope_skips_non_students(monkeypatch):
    faculty = {**_student(), "role": "faculty"}
    query = lambda *_: (_ for _ in ()).throw(AssertionError("unexpected query"))
    monkeypatch.setattr(seed_identity_map.db_conn, "query", query)

    assert seed_identity_map.sync_academic_scope(faculty, dry_run=False) == "SKIP"
