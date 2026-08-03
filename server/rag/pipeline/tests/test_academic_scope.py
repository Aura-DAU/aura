import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from api.auth import Identity
from api.academic_scope_persist import (
    derive_academic_identity,
    map_dept_to_programme,
    upsert_student_academic_scope,
)
from api.request_context import AcademicScope, AcademicScopeResolver
from pipeline.aura_chat import ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE, RETRIEVAL_FAILURE_RESPONSE
from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline


def scope() -> AcademicScope:
    return AcademicScope(
        erp_id="202401001",
        identity_version=1,
        admission_year=2024,
        programme_id="btech-ict",
        branch_id=None,
        department_id="ICT",
        degree_level="undergraduate",
        profile_version=1,
        academic_status="active",
        expected_graduation_year=2028,
        curriculum_version=None,
        regulation_version=None,
        enrollment_snapshot_id=None,
        current_semester=3,
        registered_course_codes=("IT205",),
        elective_course_codes=(),
        profile_stale=False,
        enrollment_stale=False,
    )


def test_scope_allows_global_and_matching_curriculum():
    academic_scope = scope()
    assert academic_scope.document_is_eligible({"applicability_scope": "global"})
    assert academic_scope.document_is_eligible({
        "applicability_scope": "curriculum",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": 2021,
        "admission_year_to": 9999,
    })


def test_scope_rejects_other_programme_and_unclassified_academic_documents():
    academic_scope = scope()
    assert not academic_scope.document_is_eligible({
        "applicability_scope": "curriculum",
        "programme_id": "btech-mnc",
        "degree_level": "undergraduate",
        "admission_year_from": 2021,
        "admission_year_to": 9999,
    })
    assert not academic_scope.document_is_eligible({"applicability_scope": "unclassified"})


def test_scope_rejects_out_of_range_curriculum():
    academic_scope = scope()
    assert not academic_scope.document_is_eligible({
        "applicability_scope": "curriculum",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": 2025,
        "admission_year_to": 9999,
    })


def test_scope_allows_course_docs_regardless_of_enrollment():
    # Course docs are public course-catalog information: a signed-in student
    # may look up any course, even one they are not registered for.
    academic_scope = scope()
    assert academic_scope.document_is_eligible({
        "applicability_scope": "course",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": 2021,
        "admission_year_to": 9999,
        "course_code": "IT999",
    })


def test_resolver_falls_back_to_no_scope_when_db_lookup_fails(monkeypatch):
    import db.connection as db_conn

    def explode(*args, **kwargs):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(db_conn, "query", explode)

    resolver = AcademicScopeResolver()
    ctx = resolver.resolve(Identity(erp_id="202401001", role="student"), "student")

    assert ctx.academic_scope is None


def test_retrieval_pipeline_handles_missing_vector_index():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    pipeline.retriever = SimpleNamespace(
        index=None,
        model=SimpleNamespace(encode=lambda *args, **kwargs: None),
        retrieve=lambda *args, **kwargs: [],
    )

    results = pipeline._retrieve_dual_path("what is the policy", {"entities": {}}, allowed_roles=None, academic_scope=None)

    assert results == []


def test_map_dept_ict_and_ictcs_to_btech_ict():
    assert map_dept_to_programme("ICT") == ("btech-ict", "undergraduate")
    assert map_dept_to_programme("ICTCS") == ("btech-ict", "undergraduate")


def test_map_dept_other_programmes():
    assert map_dept_to_programme("MnC") == ("btech-mnc", "undergraduate")
    assert map_dept_to_programme("EVD") == ("btech-evd", "undergraduate")
    assert map_dept_to_programme("MTech") == ("mtech-ict", "postgraduate")
    assert map_dept_to_programme("MScIT") == ("msc-it", "postgraduate")
    assert map_dept_to_programme("MScDS") == ("msc-ds", "postgraduate")
    assert map_dept_to_programme("PhD") == ("phd", "doctoral")
    assert map_dept_to_programme("UNKNOWN") is None
    assert map_dept_to_programme(None) is None


def test_derive_academic_identity_from_erp_and_dept():
    ict = derive_academic_identity(erp_id="202401001", dept="ICT")
    assert ict is not None
    assert ict.programme_id == "btech-ict"
    assert ict.admission_year == 2024
    assert ict.degree_level == "undergraduate"
    assert ict.department_id == "ICT"
    assert ict.branch_id is None
    assert ict.expected_graduation_year == 2028

    ictcs = derive_academic_identity(erp_id="202401401", dept="ICTCS")
    assert ictcs is not None
    assert ictcs.programme_id == "btech-ict"
    assert ictcs.department_id == "ICTCS"
    assert ictcs.branch_id == "ict-cs"


def test_upsert_student_academic_scope_writes_identity_and_profile(monkeypatch):
    import db.connection as db_conn

    calls = []

    def fake_execute(sql, params=()):
        calls.append((sql, params))

    monkeypatch.setattr(db_conn, "execute", fake_execute)

    assert upsert_student_academic_scope(erp_id="202401001", dept="ICT") is True
    assert len(calls) == 2
    identity_sql, identity_params = calls[0]
    profile_sql, profile_params = calls[1]
    assert "INSERT INTO student_identity" in identity_sql
    assert identity_params[0] == "202401001"
    assert identity_params[1] == 2024
    assert identity_params[2] == "btech-ict"
    assert identity_params[5] == "undergraduate"
    assert "INSERT INTO student_academic_profile" in profile_sql
    assert profile_params[0] == "202401001"
    assert profile_params[1] == 2028


def test_upsert_returns_false_when_dept_unknown(monkeypatch):
    import db.connection as db_conn

    monkeypatch.setattr(db_conn, "execute", MagicMock())
    assert upsert_student_academic_scope(erp_id="202401001", dept="UNKNOWN") is False
    db_conn.execute.assert_not_called()


def test_resolver_backfills_scope_when_tables_empty(monkeypatch):
    import db.connection as db_conn

    scope_row = {
        "identity_version": 1,
        "admission_year": 2024,
        "programme_id": "btech-ict",
        "branch_id": None,
        "department_id": "ICT",
        "degree_level": "undergraduate",
        "profile_version": 1,
        "academic_status": "active",
        "expected_graduation_year": 2028,
        "curriculum_version": None,
        "regulation_version": None,
        "synced_at": None,
        "enrollment_snapshot_id": None,
        "current_semester": None,
        "enrollment_captured_at": None,
    }
    query_calls = {"n": 0}

    def fake_query(sql, params=()):
        query_calls["n"] += 1
        if query_calls["n"] == 1:
            return []
        return [scope_row]

    monkeypatch.setattr(db_conn, "query", fake_query)
    monkeypatch.setattr(
        "api.academic_scope_persist.ensure_student_academic_scope",
        lambda identity: True,
    )

    resolver = AcademicScopeResolver()
    ctx = resolver.resolve(
        Identity(erp_id="202401001", role="student", dept="ICT"),
        "student",
    )

    assert ctx.academic_scope is not None
    assert ctx.academic_scope.programme_id == "btech-ict"
    assert ctx.academic_scope.admission_year == 2024


def test_public_rag_empty_uses_scope_unavailable_message():
    from pipeline.aura_chat_graph import AuraChatGraph

    graph = AuraChatGraph.__new__(AuraChatGraph)
    graph.pipeline = SimpleNamespace(
        get_context=lambda *args, **kwargs: {
            "chunks": [],
            "context": "",
            "sources": [],
            "abstention_reason": "academic_scope_unavailable",
        }
    )

    state = {
        "query": "what is the ICT curriculum?",
        "history": [],
        "query_type": "PUBLIC",
        "request_context": SimpleNamespace(effective_role="student"),
        "academic_scope": None,
    }
    out = AuraChatGraph._n_public_rag(graph, state)
    assert out["result"]["answer"] == ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE


def test_public_rag_empty_uses_generic_retrieval_failure_otherwise():
    from pipeline.aura_chat_graph import AuraChatGraph

    graph = AuraChatGraph.__new__(AuraChatGraph)
    graph.pipeline = SimpleNamespace(
        get_context=lambda *args, **kwargs: {
            "chunks": [],
            "context": "",
            "sources": [],
        }
    )

    state = {
        "query": "campus wifi?",
        "history": [],
        "query_type": "PUBLIC",
        "request_context": SimpleNamespace(effective_role="student"),
        "academic_scope": None,
    }
    out = AuraChatGraph._n_public_rag(graph, state)
    assert out["result"]["answer"] == RETRIEVAL_FAILURE_RESPONSE
