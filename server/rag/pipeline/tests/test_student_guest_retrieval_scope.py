from types import SimpleNamespace
from unittest.mock import MagicMock

from api.request_context import AcademicScope
from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline


class _ImmediateFuture:
    def __init__(self, value):
        self._value = value

    def result(self):
        return self._value


class _ImmediateExecutor:
    def submit(self, function, *args):
        return _ImmediateFuture(function(*args))


def _scope(course_codes=(), enrollment_snapshot_id=None):
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
        enrollment_snapshot_id=enrollment_snapshot_id,
        current_semester=3,
        registered_course_codes=course_codes,
        elective_course_codes=(),
        profile_stale=False,
        enrollment_stale=False,
    )


def _contains_field(metadata_filter, field):
    if not isinstance(metadata_filter, dict):
        return False
    if field in metadata_filter:
        return True
    return any(
        _contains_field(item, field)
        for value in metadata_filter.values()
        if isinstance(value, list)
        for item in value
    )


def _pipeline_for_get_context(plan):
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    pipeline.executor = _ImmediateExecutor()
    pipeline.planner = SimpleNamespace(plan=lambda *args: plan)
    pipeline.rewriter = MagicMock()
    pipeline._retrieve_dual_path = MagicMock(return_value=[])
    pipeline.entity_retriever = None
    pipeline.reranker = SimpleNamespace(rerank=lambda **kwargs: [])
    pipeline.builder = SimpleNamespace(
        build=lambda *args, **kwargs: {
            "context": "<context>\n</context>",
            "sources": [],
        }
    )
    pipeline.chunk_by_coordinate = {}
    return pipeline


def test_generic_student_query_reuses_speculation_without_hard_program_filter():
    plan = {
        "top_k": 5,
        "entities": {},
        "retrieval_intent": "general",
        "query_decomposition": [],
        "retrieval_hints": {},
        "expanded_terms": [],
    }
    pipeline = _pipeline_for_get_context(plan)

    result = pipeline.get_context(
        "What is the hostel policy?",
        user_role="student",
        academic_scope=_scope(),
    )

    pipeline._retrieve_dual_path.assert_called_once()
    speculative_plan = pipeline._retrieve_dual_path.call_args.args[1]
    assert speculative_plan.get("entities", {}) == {}
    assert speculative_plan["scope_entities"]["program_name"] == "B.Tech. (ICT)"
    assert result["plan"]["entities"] == {}
    assert pipeline._build_metadata_filter(result["plan"]) is None


def test_explicit_programme_query_retains_hard_filter():
    plan = {
        "top_k": 5,
        "entities": {"program_name": "B.Tech. (MnC)"},
        "entity_confidence": 0.95,
        "retrieval_intent": "program_overview",
        "query_decomposition": [],
        "retrieval_hints": {},
        "expanded_terms": [],
    }
    pipeline = _pipeline_for_get_context(plan)

    result = pipeline.get_context(
        "Tell me about B.Tech MnC",
        user_role="student",
        academic_scope=_scope(),
    )

    assert pipeline._retrieve_dual_path.call_count == 2
    assert result["plan"]["entities"]["program_name"] == "B.Tech. (MnC)"
    assert pipeline._build_metadata_filter(result["plan"]) == {
        "program_name": {"$in": ["B.Tech. (MnC)"]}
    }


def test_semantic_entity_fallback_preserves_authorization_and_academic_scope():
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    index = MagicMock()
    index.query.side_effect = [
        {
            "matches": [
                {
                    "id": "filtered",
                    "score": 0.9,
                    "metadata": {"applicability_scope": "global"},
                }
            ]
        },
        {
            "matches": [
                {
                    "id": "fallback",
                    "score": 0.8,
                    "metadata": {"applicability_scope": "global"},
                }
            ]
        },
    ]
    pipeline.retriever = SimpleNamespace(
        index=index,
        embed_query=lambda query: [0.1],
        retrieve=lambda **kwargs: [],
    )
    plan = {
        "top_k": 5,
        "entities": {"program_name": "B.Tech. (ICT)"},
        "entity_confidence": 0.95,
    }

    results = pipeline._retrieve_dual_path(
        "ICT rules",
        plan,
        allowed_roles=["public", "student"],
        academic_scope=_scope(),
    )

    assert {result["id"] for result in results} == {"filtered", "fallback"}
    assert index.query.call_count == 2
    initial_filter = index.query.call_args_list[0].kwargs["filter"]
    fallback_filter = index.query.call_args_list[1].kwargs["filter"]
    assert _contains_field(initial_filter, "program_name")
    assert not _contains_field(fallback_filter, "program_name")
    assert _contains_field(fallback_filter, "authorization")
    assert _contains_field(fallback_filter, "applicability_scope")
    assert _contains_field(fallback_filter, "programme_id")


def test_registrations_admit_course_scope_regardless_of_enrollment():
    unavailable_scope = _scope()
    empty_snapshot_scope = _scope(enrollment_snapshot_id="snapshot-1")
    populated_scope = _scope(("IT205",))
    it205 = {"applicability_scope": "course", "course_code": "IT205"}
    it999 = {"applicability_scope": "course", "course_code": "IT999"}

    assert unavailable_scope.document_is_eligible(it999)
    assert empty_snapshot_scope.document_is_eligible(it205)
    assert empty_snapshot_scope.document_is_eligible(it999)
    assert populated_scope.document_is_eligible(it205)
    assert populated_scope.document_is_eligible(it999)

    empty_filter = RetrievalPipeline._academic_scope_filter(empty_snapshot_scope)
    populated_filter = RetrievalPipeline._academic_scope_filter(populated_scope)
    assert not _contains_field(empty_filter, "course_code")
    assert not _contains_field(populated_filter, "course_code")
