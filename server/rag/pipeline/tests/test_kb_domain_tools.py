"""
test_kb_domain_tools.py — Unit tests for domain KB retrieval skills.

Mocks RetrievalPipeline.get_context and KeyManager.call_with_rotation,
mirroring test_community_tools.py.
"""

import pytest

from pipeline.ecampus import (
    academic_kb_tools,
    admin_people_kb_tools,
    campus_info_kb_tools,
    kb_retrieval,
    research_careers_kb_tools,
)
from pipeline.ecampus.tool_registry import TOOL_REGISTRY, tools_for_role, PUBLIC_KB_TOOL_NAMES


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
    sources = sources or ["sample_kb.md"]

    class DummyPipeline:
        def get_context(self, query, user_role=None, academic_scope=None):
            self.last = {
                "query": query,
                "user_role": user_role,
                "academic_scope": academic_scope,
            }
            return {"context": context, "sources": sources}

    pipeline = DummyPipeline()
    monkeypatch.setattr(kb_retrieval, "get_retrieval_pipeline", lambda: pipeline)
    return pipeline


def _patch_llm(monkeypatch, content: str = "ok"):
    monkeypatch.setattr(
        kb_retrieval.KeyManager,
        "call_with_rotation",
        staticmethod(lambda fn, max_retries=3: _FakeResponse(content)),
    )


# Tools expected in registry, grouped loosely by domain.
_KB_TOOLS = (
    "lookup_academic_calendar",
    "lookup_course_policy",
    "lookup_academic_requirements",
    "lookup_admissions_info",
    "lookup_public_timetable_docs",
    "lookup_university_policy",
    "lookup_faculty_profile",
    "search_people_directory",
    "lookup_research_info",
    "lookup_placement_careers_info",
    "lookup_campus_events_notices",
    "lookup_campus_facilities",
    "lookup_student_services_info",
    "lookup_alumni_info",
    "lookup_achievements",
    "lookup_cep_info",
)


def test_kb_domain_tools_registered_and_role_gated():
    for name in _KB_TOOLS:
        assert name in TOOL_REGISTRY
        assert "student" in TOOL_REGISTRY[name].allowed_roles
        assert "faculty" in TOOL_REGISTRY[name].allowed_roles

    student_names = {t.name for t in tools_for_role("student")}
    faculty_names = {t.name for t in tools_for_role("faculty")}
    for name in _KB_TOOLS:
        assert name in student_names
        assert name in faculty_names
        assert name in PUBLIC_KB_TOOL_NAMES

    # Existing workflow tools still preferred / present
    assert "certificate_request_guidance" in student_names
    assert "seed_grant_guidance" in faculty_names
    assert "search_student_clubs" in student_names
    # Personal ERP tools stay out of the public-KB orchestrator set.
    assert "get_cgpa" not in PUBLIC_KB_TOOL_NAMES


def test_lookup_academic_calendar(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Autumn 2026-27 mid-semester exams begin 15 September 2026.",
        sources=["academic_calendar_2026_27_v2.md"],
    )
    _patch_llm(monkeypatch, "Mid-sem exams: 15 September 2026 (Autumn 2026-27).")
    result = academic_kb_tools.handle_lookup_academic_calendar(
        student_identity(), topic="mid semester exams",
    )
    assert "September" in result["response"] or "mid" in result["response"].lower()
    assert "academic calendar" in pipeline.last["query"].lower()
    assert pipeline.last["user_role"] == "student"
    assert result["sources"]


def test_lookup_course_policy(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "IT623 Data Structures. Evaluation: 30% mid, 50% end, 20% labs. Instructor: Prof. X.",
        sources=["IT623_Data_Structures_Autumn25.md"],
    )
    _patch_llm(monkeypatch, "IT623 — Evaluation: 30/50/20. Instructor: Prof. X.")
    result = academic_kb_tools.handle_lookup_course_policy(
        student_identity(), course="IT623",
    )
    assert "IT623" in result["response"] or "30" in result["response"]
    assert "IT623" in pipeline.last["query"]
    assert "course policy" in pipeline.last["query"].lower()


def test_lookup_course_policy_requires_name():
    result = academic_kb_tools.handle_lookup_course_policy(student_identity(), course="")
    assert "provide" in result["response"].lower()


def test_lookup_academic_requirements(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "BTech ICT requires minimum 150 credits for graduation under 2021-22 rules.",
        sources=["academic_policy_academic_requirements_btech_ict_wef_2021-22.md"],
    )
    _patch_llm(monkeypatch, "BTech ICT: 150 credits (2021-22 rules).")
    result = academic_kb_tools.handle_lookup_academic_requirements(
        student_identity(), program="BTech ICT",
    )
    assert "150" in result["response"] or "BTech" in result["response"]
    assert "academic requirements" in pipeline.last["query"].lower()


def test_lookup_admissions_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "MDes admissions require a valid CEED score. Application via admissions portal.",
        sources=["admissions_mdes.md"],
    )
    _patch_llm(monkeypatch, "MDes: CEED required. Apply via admissions portal.")
    result = academic_kb_tools.handle_lookup_admissions_info(
        student_identity(), topic="MDes",
    )
    assert "CEED" in result["response"] or "MDes" in result["response"]
    assert "admissions" in pipeline.last["query"].lower()


def test_lookup_public_timetable_docs(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "CS-AI 1st Yr Sec A: Monday 9am IT101 Room LT1.",
        sources=["CS-AI_1st_Yr_Sec_A.md"],
    )
    _patch_llm(monkeypatch, "CS-AI Sec A: Mon 9am IT101 LT1.")
    result = academic_kb_tools.handle_lookup_public_timetable_docs(
        student_identity(), program="CS-AI 1st year section A",
    )
    assert result["response"]
    assert "timetable" in pipeline.last["query"].lower()


def test_lookup_university_policy_student(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Attendance policy: minimum 80% attendance required for exam eligibility.",
        sources=["attendance_policy_v2.md"],
    )
    _patch_llm(monkeypatch, "Minimum 80% attendance for exam eligibility.")
    result = admin_people_kb_tools.handle_lookup_university_policy(
        student_identity(), topic="attendance",
    )
    assert "80" in result["response"]
    assert pipeline.last["user_role"] == "student"


def test_lookup_university_policy_faculty_uses_faculty_retrieval(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Faculty evaluation rubric includes research output and teaching quality.",
        sources=["faculty_evaluation_rubric.md"],
    )
    _patch_llm(monkeypatch, "Evaluation: research output + teaching quality.")
    result = admin_people_kb_tools.handle_lookup_university_policy(
        faculty_identity(), topic="faculty evaluation",
    )
    assert result["response"]
    assert pipeline.last["user_role"] == "faculty_general"


def test_lookup_university_policy_requires_topic():
    result = admin_people_kb_tools.handle_lookup_university_policy(
        student_identity(), topic="",
    )
    assert "provide" in result["response"].lower()


def test_lookup_faculty_profile(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Prof. Kalyan Sasidhar. Associate Professor. Research: IoT, sensing.",
        sources=["faculty_profile_kalyan_sasidhar.md"],
    )
    _patch_llm(monkeypatch, "Kalyan Sasidhar — Associate Professor. IoT, sensing.")
    result = admin_people_kb_tools.handle_lookup_faculty_profile(
        student_identity(), name="Kalyan Sasidhar",
    )
    assert "Kalyan" in result["response"] or "IoT" in result["response"]
    assert "faculty profile" in pipeline.last["query"].lower()


def test_search_people_directory(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Teaching fellows list includes several ICT fellows.",
        sources=["teaching_fellows_list.md"],
    )
    _patch_llm(monkeypatch, "- Teaching fellows in ICT (see list).")
    result = admin_people_kb_tools.handle_search_people_directory(
        student_identity(), query="teaching fellows",
    )
    assert result["response"]
    assert "faculty" in pipeline.last["query"].lower() or "fellows" in pipeline.last["query"].lower()


def test_lookup_research_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "AI/ML and Data Science research area covers ML, NLP, and vision labs.",
        sources=["ai_ml_and_data_science.md"],
    )
    _patch_llm(monkeypatch, "AI/ML research: ML, NLP, vision.")
    result = research_careers_kb_tools.handle_lookup_research_info(
        student_identity(), topic="AI ML",
    )
    assert "ML" in result["response"] or "AI" in result["response"]
    assert "research" in pipeline.last["query"].lower()


def test_lookup_placement_careers_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Placement process: resume submission, PPT, interviews. Dream category rules apply.",
        sources=["placement_process_steps_v2.md"],
    )
    _patch_llm(monkeypatch, "1. Resume 2. PPT 3. Interviews. Dream category rules apply.")
    result = research_careers_kb_tools.handle_lookup_placement_careers_info(
        student_identity(), topic="placement process",
    )
    assert "Resume" in result["response"] or "placement" in result["response"].lower()
    assert "placement" in pipeline.last["query"].lower()


def test_lookup_campus_events_notices(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Tarang 2025 annual Navratri celebration at DAU.",
        sources=["tarang_2025_the_annual_navratri_celebration_at_dhirubhai_ambani_university.md"],
    )
    _patch_llm(monkeypatch, "Tarang 2025 — annual Navratri celebration.")
    result = campus_info_kb_tools.handle_lookup_campus_events_notices(
        student_identity(), topic="Tarang",
    )
    assert "Tarang" in result["response"]
    assert "event" in pipeline.last["query"].lower()


def test_lookup_campus_facilities(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Sports complex includes indoor courts and a gymnasium.",
        sources=["sports_complex_v2.md"],
    )
    _patch_llm(monkeypatch, "Sports complex: indoor courts and gymnasium.")
    result = campus_info_kb_tools.handle_lookup_campus_facilities(
        student_identity(), topic="sports",
    )
    assert "gym" in result["response"].lower() or "sports" in result["response"].lower()
    assert "facility" in pipeline.last["query"].lower() or "sports" in pipeline.last["query"].lower()


def test_lookup_student_services_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Medical assistance SOP: contact campus medical facility for emergencies.",
        sources=["medical_assistance_sop.md"],
    )
    _patch_llm(monkeypatch, "Emergencies: contact campus medical facility.")
    result = campus_info_kb_tools.handle_lookup_student_services_info(
        student_identity(), topic="medical",
    )
    assert "medical" in result["response"].lower()
    assert "student services" in pipeline.last["query"].lower()


def test_lookup_alumni_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "Alumni Pankaj Mangal, batch profile published on alumni portal.",
        sources=["alumni_pankaj_mangal.md"],
    )
    _patch_llm(monkeypatch, "Pankaj Mangal — alumni profile available.")
    result = campus_info_kb_tools.handle_lookup_alumni_info(
        student_identity(), topic="Pankaj Mangal",
    )
    assert "Pankaj" in result["response"] or "alumni" in result["response"].lower()


def test_lookup_achievements(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "ACM SIGAPP STAP grant awarded to DA-IICT students.",
        sources=["acm_sigapp_stap_grant.md"],
    )
    _patch_llm(monkeypatch, "ACM SIGAPP STAP grant — student achievement.")
    result = campus_info_kb_tools.handle_lookup_achievements(
        student_identity(), topic="ACM SIGAPP",
    )
    assert "ACM" in result["response"] or "grant" in result["response"].lower()


def test_lookup_cep_info(monkeypatch):
    pipeline = _patch_retrieval(
        monkeypatch,
        "CEP offers continuing education courses through AIP proposals.",
        sources=["cep_full_policy_module.md"],
    )
    _patch_llm(monkeypatch, "CEP: continuing education via AIP course proposals.")
    result = campus_info_kb_tools.handle_lookup_cep_info(
        student_identity(), topic="AIP",
    )
    assert "CEP" in result["response"] or "AIP" in result["response"]
    assert "CEP" in pipeline.last["query"] or "cep" in pipeline.last["query"].lower()


def test_empty_kb_returns_friendly_message(monkeypatch):
    _patch_retrieval(monkeypatch, "")
    result = academic_kb_tools.handle_lookup_academic_calendar(
        student_identity(), topic="nonexistent",
    )
    assert result["sources"] == []
    assert "couldn't find" in result["response"].lower() or "knowledge base" in result["response"].lower()


def test_kb_tools_deny_unrelated_role():
    with pytest.raises(PermissionError):
        academic_kb_tools.handle_lookup_course_policy(
            {"erp_id": "X1", "role": "public"}, course="IT623",
        )
