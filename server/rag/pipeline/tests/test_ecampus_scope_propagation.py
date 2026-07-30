from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from api.request_context import AcademicScope, AcademicScopeResolver, RequestContext
from pipeline.ecampus import scholarship_tools, student_workflow_tools


class _Identity:
    def __init__(self, role, erp_id="S1"):
        self.role = role
        self.erp_id = erp_id

    def as_dict(self):
        return {"role": self.role, "erp_id": self.erp_id}


def _scope() -> AcademicScope:
    return AcademicScope(
        erp_id="S1",
        identity_version=1,
        admission_year=2024,
        programme_id="btech-ict",
        branch_id="ict",
        department_id="ICT",
        degree_level="undergraduate",
        profile_version=2,
        academic_status="active",
        expected_graduation_year=2028,
        curriculum_version="2023",
        regulation_version="R1",
        enrollment_snapshot_id="snap-1",
        current_semester=3,
        registered_course_codes=("IT205",),
        elective_course_codes=(),
        profile_stale=False,
        enrollment_stale=False,
    )


def test_scholarship_tool_uses_request_context_scope(monkeypatch):
    captured = {}

    class DummyPipeline:
        def get_context(self, query, user_role=None, academic_scope=None):
            captured["user_role"] = user_role
            captured["academic_scope"] = academic_scope
            return {"context": "policy context", "sources": []}

    monkeypatch.setattr(scholarship_tools, "_get_retrieval_pipeline", lambda: DummyPipeline())
    monkeypatch.setattr(
        scholarship_tools.InferenceRouter,
        "call_with_rotation",
        staticmethod(lambda fn, max_retries=3: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"eligible_schemes":[],"general_guidelines":[]}'))])),
    )

    request_context = RequestContext(
        identity=_Identity("student", "S1"),
        effective_role="student",
        academic_scope=_scope(),
    )

    scholarship_tools.screen_scholarship_eligibility(
        {"erp_id": "S1", "role": "student"},
        request_context=request_context,
    )

    assert captured["user_role"] == "student"
    assert captured["academic_scope"] is request_context.academic_scope


def test_student_workflow_tool_uses_request_context_scope(monkeypatch):
    captured = {}

    class DummyPipeline:
        def get_context(self, query, user_role=None, academic_scope=None):
            captured["user_role"] = user_role
            captured["academic_scope"] = academic_scope
            return {"context": "policy context", "sources": []}

    monkeypatch.setattr(student_workflow_tools, "_get_retrieval_pipeline", lambda: DummyPipeline())
    monkeypatch.setattr(
        student_workflow_tools.KeyManager,
        "call_with_rotation",
        staticmethod(lambda fn, max_retries=3: SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="done"))])),
    )

    request_context = RequestContext(
        identity=_Identity("student", "S1"),
        effective_role="student",
        academic_scope=_scope(),
    )

    student_workflow_tools.handle_certificate_request_guidance(
        {"erp_id": "S1", "role": "student"},
        document_type="transcript",
        request_context=request_context,
    )

    assert captured["user_role"] == "student"
    assert captured["academic_scope"] is request_context.academic_scope


def test_resolver_enqueues_refresh_for_stale_scope(monkeypatch):
    import db.connection as db_conn

    rows = [{
        "identity_version": 1,
        "admission_year": 2024,
        "programme_id": "btech-ict",
        "branch_id": "ict",
        "department_id": "ICT",
        "degree_level": "undergraduate",
        "profile_version": 2,
        "academic_status": "active",
        "expected_graduation_year": 2028,
        "curriculum_version": "2023",
        "regulation_version": "R1",
        "synced_at": datetime.now(timezone.utc) - timedelta(hours=48),
        "enrollment_snapshot_id": 7,
        "current_semester": 3,
        "enrollment_captured_at": datetime.now(timezone.utc) - timedelta(hours=8),
    }]

    def fake_query(sql, params=()):
        if "student_course_enrollment" in sql:
            return []
        return rows

    monkeypatch.setattr(db_conn, "query", fake_query)
    monkeypatch.setattr(db_conn, "execute", lambda *args, **kwargs: None)

    refresh_calls = []
    monkeypatch.setattr("api.request_context._enqueue_scope_refresh", lambda erp_id: refresh_calls.append(erp_id))

    resolver = AcademicScopeResolver()
    ctx = resolver.resolve(_Identity("student", "S1"), "student")

    assert ctx.academic_scope is not None
    assert ctx.academic_scope.profile_stale is True
    assert refresh_calls == ["S1"]
