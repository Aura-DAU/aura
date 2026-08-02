"""
test_community_tools.py — Unit tests for clubs / committees / roster tools.

Mocks RetrievalPipeline.get_context and KeyManager.call_with_rotation,
mirroring test_ecampus_scope_propagation.py / student_workflow patterns.
"""

from types import SimpleNamespace
from datetime import date

import pytest

from pipeline.ecampus import community_tools
from pipeline.ecampus.tool_registry import (
    TOOL_REGISTRY,
    COMMUNITY_TOOL_NAMES,
    community_tools_for_role,
    tools_for_role,
)


def student_identity(erp_id="S1"):
    return {"erp_id": erp_id, "role": "student", "dept": "ICT"}


def faculty_identity(erp_id="F1"):
    return {"erp_id": erp_id, "role": "faculty", "dept": "ICT"}


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


def _patch_retrieval(monkeypatch, context: str, sources: list[str] | None = None):
    sources = sources or ["sbg_club_committee_c_dcs_information_2026_27.md"]

    class DummyPipeline:
        def get_context(self, query, user_role=None, academic_scope=None):
            self.last = {
                "query": query,
                "user_role": user_role,
                "academic_scope": academic_scope,
            }
            return {"context": context, "sources": sources}

    pipeline = DummyPipeline()
    monkeypatch.setattr(community_tools, "_get_retrieval_pipeline", lambda: pipeline)
    return pipeline


def _patch_llm(monkeypatch, content: str = "ok"):
    monkeypatch.setattr(
        community_tools.KeyManager,
        "call_with_rotation",
        staticmethod(lambda fn, max_retries=3: _FakeResponse(content)),
    )


def test_new_club_tools_registered_and_role_gated():
    for name in (
        "search_student_clubs",
        "get_student_club_info",
        "get_club_members",
        "lookup_club_office_bearers",
        "event_club_registration_guidance",
    ):
        assert name in TOOL_REGISTRY
        assert "student" in TOOL_REGISTRY[name].allowed_roles

    student_names = {t.name for t in tools_for_role("student")}
    assert "get_club_members" in student_names
    assert "lookup_club_office_bearers" in student_names
    assert "search_faculty_committees" not in student_names

    faculty_names = {t.name for t in tools_for_role("faculty")}
    assert "search_faculty_committees" in faculty_names
    assert "faculty_committee_responsibilities" in faculty_names
    assert "get_club_members" in faculty_names

    community_only = {t.name for t in community_tools_for_role("student")}
    assert community_only <= COMMUNITY_TOOL_NAMES
    assert "get_cgpa" not in community_only


def test_search_student_clubs(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Programming Club convenor Mahek Kanani. AI Club convenor Vedant Shah.",
    )
    _patch_llm(monkeypatch, "Programming Club — Mahek Kanani\nAI Club — Vedant Shah")
    result = community_tools.handle_search_student_clubs(
        student_identity(), topic="coding AI",
    )
    assert "Programming Club" in result["response"] or "AI Club" in result["response"]
    assert result["sources"]
    assert "club" in pipeline.last["query"].lower()
    assert pipeline.last["user_role"] == "student"


def test_get_student_club_info(monkeypatch):
    _patch_retrieval(
        monkeypatch,
        "Programming Club purpose: competitive coding. Convenor: Mahek Kanani. "
        "Email: programming-club@dau.ac.in. Join via SBG.",
    )
    _patch_llm(monkeypatch, "Purpose: competitive coding\nConvenor: Mahek Kanani")
    result = community_tools.handle_get_student_club_info(
        student_identity(), club_name="Programming Club",
    )
    assert "Mahek" in result["response"] or "coding" in result["response"].lower()


def test_get_club_members_uses_roster_query(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Club/Committee: Programming Club | Name: Mahek Kanani | Position: Convenor\n"
        "Club/Committee: Programming Club | Name: Raj Patel | Position: Dy. Convenor\n"
        "Club/Committee: Programming Club | Name: A Student | Position: Member",
        sources=["sbg_list_of_club_committee_core_members_winter_2026.md"],
    )
    _patch_llm(
        monkeypatch,
        "Office-bearers:\n- Convenor: Mahek Kanani\n- Dy. Convenor: Raj Patel\n"
        "Members:\n- A Student",
    )
    result = community_tools.handle_get_club_members(
        student_identity(), club_name="Programming Club",
    )
    assert "Mahek" in result["response"]
    assert "roster" in pipeline.last["query"].lower() or "member" in pipeline.last["query"].lower()
    assert "core members" in pipeline.last["query"].lower() or "Club Committee" in pipeline.last["query"]


def test_lookup_club_office_bearers(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Email: programming-club@dau.ac.in | Club/Committee Name: Programming Club | "
        "Convener Name: Mahek Kanani | Dy. Convener Name: Raj Patel | "
        "Faculty Mentor Name: Prof. PM jat",
    )
    _patch_llm(
        monkeypatch,
        "Convenor: Mahek Kanani\nDy. Convenor: Raj Patel\n"
        "Faculty Mentor: Prof. PM jat\nEmail: programming-club@dau.ac.in",
    )
    result = community_tools.handle_lookup_club_office_bearers(
        student_identity(), club_name="Programming Club",
    )
    assert "Mahek" in result["response"]
    assert "convenor" in pipeline.last["query"].lower()
    assert "C_DCs" in pipeline.last["query"] or "office" in pipeline.last["query"].lower()
    assert community_tools._current_academic_year() in pipeline.last["query"]


def test_current_academic_year_rolls_over_in_july():
    assert community_tools._current_academic_year(date(2026, 6, 30)) == "2025-26"
    assert community_tools._current_academic_year(date(2026, 7, 1)) == "2026-27"


def test_get_club_members_empty_kb(monkeypatch):
    _patch_retrieval(monkeypatch, "")
    result = community_tools.handle_get_club_members(
        student_identity(), club_name="Nonexistent Club",
    )
    assert result["sources"] == []
    assert "couldn't find" in result["response"].lower() or "knowledge base" in result["response"].lower()


def test_get_club_members_requires_name():
    result = community_tools.handle_get_club_members(student_identity(), club_name="")
    assert "provide" in result["response"].lower()


def test_club_member_tools_deny_unrelated_role():
    with pytest.raises(PermissionError):
        community_tools.handle_get_club_members(
            {"erp_id": "X1", "role": "public"}, club_name="Programming Club",
        )


def test_faculty_committee_responsibilities(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "BTP Committee Terms of Reference. Mandate: oversee BTech projects. "
        "Convenor: Prof. P M Jat.",
        sources=["btp_committee_tor.md"],
    )
    _patch_llm(monkeypatch, "1. Mandate: oversee BTech projects\n2. Composition: UG Committee")
    result = community_tools.handle_faculty_committee_responsibilities(
        faculty_identity(), committee_name="BTP Committee",
    )
    assert "BTech" in result["response"] or "Mandate" in result["response"] or "projects" in result["response"].lower()
    assert pipeline.last["user_role"] == "faculty_general"


def test_faculty_committee_denies_student():
    with pytest.raises(PermissionError):
        community_tools.handle_faculty_committee_responsibilities(
            student_identity(), committee_name="BTP Committee",
        )


def test_search_faculty_committees(monkeypatch):
    _patch_retrieval(
        monkeypatch,
        "Exam Committee ToR. Research Committee ToR. Placement Committee ToR.",
        sources=["exam_committee_tor.md"],
    )
    _patch_llm(monkeypatch, "- Exam Committee\n- Research Committee\n- Placement Committee")
    result = community_tools.handle_search_faculty_committees(
        faculty_identity(), topic="examinations research",
    )
    assert "Exam" in result["response"] or "Research" in result["response"]


def test_event_club_registration_guidance(monkeypatch):
    _patch_retrieval(
        monkeypatch,
        "To join Music Club contact music_club@dau.ac.in. Registration via SBG.",
    )
    _patch_llm(monkeypatch, "1. Email music_club@dau.ac.in\n2. Complete SBG registration")
    result = community_tools.handle_event_club_registration_guidance(
        student_identity(), name="Music Club",
    )
    assert result["response"]
    assert result["sources"]


def test_community_tool_passes_academic_scope(monkeypatch):
    from api.request_context import AcademicScope, RequestContext

    captured = {}

    class DummyPipeline:
        def get_context(self, query, user_role=None, academic_scope=None):
            captured["academic_scope"] = academic_scope
            captured["user_role"] = user_role
            return {"context": "Programming Club convenor listed.", "sources": ["x.md"]}

    monkeypatch.setattr(community_tools, "_get_retrieval_pipeline", lambda: DummyPipeline())
    _patch_llm(monkeypatch, "Convenor listed")

    scope = AcademicScope(
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
    request_context = RequestContext(
        identity=SimpleNamespace(role="student", erp_id="S1", as_dict=lambda: student_identity()),
        effective_role="student",
        academic_scope=scope,
    )
    community_tools.handle_lookup_club_office_bearers(
        student_identity(),
        club_name="Programming Club",
        request_context=request_context,
    )
    assert captured["academic_scope"] is scope
    assert captured["user_role"] == "student"
