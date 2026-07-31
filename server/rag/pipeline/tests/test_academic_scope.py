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


def test_scope_rejects_out_of_range_and_unregistered_course():
    academic_scope = scope()
    assert not academic_scope.document_is_eligible({
        "applicability_scope": "curriculum",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": 2025,
        "admission_year_to": 9999,
    })
    assert not academic_scope.document_is_eligible({
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


def test_abstention_skipped_when_plan_names_programme():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    plan = {
        "category": "academics",
        "retrieval_intent": "program_curriculum",
        "entities": {"program_name": "B.Tech ICT CS"},
    }
    assert pipeline._requires_academic_scope(plan)
    assert pipeline._has_explicit_programme_context(plan)


def test_abstention_applies_without_named_programme():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    plan = {
        "category": "academics",
        "retrieval_intent": "program_curriculum",
        "entities": {},
    }
    assert pipeline._requires_academic_scope(plan)
    assert not pipeline._has_explicit_programme_context(plan)


def test_infer_dept_from_erp_id():
    from api.academic_scope_persist import infer_dept_from_erp_id

    assert infer_dept_from_erp_id("202401401") == "ICTCS"
    assert infer_dept_from_erp_id("202401001") == "ICT"
    assert infer_dept_from_erp_id("202403001") == "MnC"
    assert infer_dept_from_erp_id("bad") is None


def test_personalized_rewrite_does_not_default_to_ict():
    from pipeline.retrieval.query_planner import rewrite_personalized_academic_query

    q = "What is the course structure for my branch?"
    assert rewrite_personalized_academic_query(q) == q
    rewritten = rewrite_personalized_academic_query(
        q, identity=SimpleNamespace(dept="MnC", program=None, programme=None, branch=None)
    )
    assert "MnC" in rewritten
    assert "ICT" not in rewritten


def test_ensure_backfill_infers_dept_when_identity_missing_dept(monkeypatch):
    from api.academic_scope_persist import ensure_student_academic_scope

    captured = {}

    def fake_upsert(*, erp_id, dept, admission_year=None):
        captured["erp_id"] = erp_id
        captured["dept"] = dept
        captured["admission_year"] = admission_year
        return True

    monkeypatch.setattr(
        "api.academic_scope_persist.upsert_student_academic_scope",
        fake_upsert,
    )
    monkeypatch.setattr(
        "api.academic_scope_persist._lookup_dept_from_identity_map",
        lambda erp_id: None,
    )

    assert ensure_student_academic_scope(
        Identity(erp_id="202401401", role="student", dept=None)
    ) is True
    assert captured["dept"] == "ICTCS"
    assert captured["admission_year"] == 2024


def test_scope_allows_string_admission_years():
    academic_scope = scope()
    assert academic_scope.document_is_eligible({
        "applicability_scope": "curriculum",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": "2021",
        "admission_year_to": "9999",
    })


def test_profile_fast_path_answers_who_am_i():
    from pipeline.aura_chat_graph import AuraChatGraph, SimpleIdentity

    graph = AuraChatGraph.__new__(AuraChatGraph)
    state = {
        "query": "Who am I?",
        "identity": SimpleIdentity({
            "erp_id": "202401001",
            "role": "student",
            "full_name": "Aarav Sharma",
            "dept": "ICT",
        }),
        "academic_scope": None,
        "result": None,
    }
    out = AuraChatGraph._n_profile_fast_path(graph, state)
    assert out["result"] is not None
    assert "Aarav Sharma" in out["result"]["answer"]
    assert out["result"]["is_personal_data"] is True


def test_community_tools_falls_through_on_empty_answer(monkeypatch):
    from pipeline.aura_chat_graph import AuraChatGraph, SimpleIdentity

    def _fake_init(self):
        self.intent_router = SimpleNamespace(classify=lambda q: "COMMUNITY")
        self.ecampus_orchestrator = SimpleNamespace(
            run=lambda **kwargs: {"answer": "", "sources": []}
        )

    monkeypatch.setattr(AuraChatGraph, "__init__", _fake_init)
    graph = AuraChatGraph()
    state = {
        "query": "What clubs for music?",
        "history": [],
        "identity": SimpleIdentity({"erp_id": "S1", "role": "student"}),
        "request_context": None,
        "result": None,
    }
    out = graph._n_community_tools(state)
    assert out.get("result") is None


def test_community_tools_falls_through_on_orchestrator_error(monkeypatch):
    from pipeline.aura_chat_graph import AuraChatGraph, SimpleIdentity

    def _boom(**kwargs):
        raise RuntimeError("orchestrator down")

    def _fake_init(self):
        self.intent_router = SimpleNamespace(classify=lambda q: "COMMUNITY")
        self.ecampus_orchestrator = SimpleNamespace(run=_boom)

    monkeypatch.setattr(AuraChatGraph, "__init__", _fake_init)
    graph = AuraChatGraph()
    state = {
        "query": "What clubs for music?",
        "history": [],
        "identity": SimpleIdentity({"erp_id": "S1", "role": "student"}),
        "request_context": None,
        "result": None,
    }
    out = graph._n_community_tools(state)
    assert out.get("result") is None
