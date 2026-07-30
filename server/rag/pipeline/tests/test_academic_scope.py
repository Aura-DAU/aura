import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from api.auth import Identity
from api.request_context import AcademicScope, AcademicScopeResolver
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
