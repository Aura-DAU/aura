"""
test_scholarship_tools.py — Tests for scholarship eligibility screening.

Mocks RetrievalPipeline.get_context and KeyManager.call_with_rotation,
following the same pattern as test_student_workflow_tools.py-style tools
elsewhere in this package (KeyManager routes the LLM call, not a direct
Groq client).
"""

import pytest
from pipeline.ecampus import scholarship_tools


def student_identity(erp_id="S1"):
    return {"erp_id": erp_id, "role": "student", "dept": "ICT"}


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


def test_screen_scholarship_eligibility(monkeypatch):
    monkeypatch.setattr(
        scholarship_tools,
        "_get_retrieval_pipeline",
        lambda: type("R", (), {
            "get_context": lambda self, query, user_role=None: {
                "context": (
                    "Institute offers Merit Scholarship to top SPI performers. "
                    "Merit-cum-Means offers a waiver to students with CGPA > 7.5 "
                    "and family income < 6 Lakh."
                ),
                "sources": ["scholarships_and_financial_aid.md"],
            },
        })(),
    )

    fake_json = (
        '{"eligible_schemes": [{"name": "Merit-cum-Means", "type": "Merit-cum-Means", '
        '"benefit": "Partial waiver", "status": "eligible", '
        '"reason_or_conditions": "Income is low and CGPA is 8.5", '
        '"mandatory_documents": ["Income Certificate"], '
        '"deadline": "Refer to Academic Office"}], '
        '"general_guidelines": ["No backlogs"]}'
    )

    def fake_call_with_rotation(fn, max_retries=3):
        return _FakeResponse(fake_json)

    monkeypatch.setattr(scholarship_tools.KeyManager, "call_with_rotation", staticmethod(fake_call_with_rotation))

    result = scholarship_tools.screen_scholarship_eligibility(
        student_identity(),
        branch="BTech ICT",
        year=2,
        category="General",
        cgpa=8.5,
        annual_income=500000.0,
    )

    assert len(result["eligible_schemes"]) == 1
    assert result["eligible_schemes"][0]["name"] == "Merit-cum-Means"
    assert result["eligible_schemes"][0]["status"] == "eligible"
    assert result["general_guidelines"] == ["No backlogs"]


def test_screen_scholarship_eligibility_denies_faculty(monkeypatch):
    with pytest.raises(PermissionError):
        scholarship_tools.screen_scholarship_eligibility(
            {"erp_id": "F1", "role": "faculty_general", "dept": "ICT"},
            branch="BTech ICT", year=2, category="General", cgpa=8.5,
        )


def test_screen_scholarship_eligibility_empty_kb(monkeypatch):
    monkeypatch.setattr(
        scholarship_tools,
        "_get_retrieval_pipeline",
        lambda: type("R", (), {
            "get_context": lambda self, query, user_role=None: {"context": "", "sources": []},
        })(),
    )
    result = scholarship_tools.screen_scholarship_eligibility(
        student_identity(), branch="BTech ICT", year=2, category="General", cgpa=8.5,
    )
    assert result["eligible_schemes"] == []
    assert result["general_guidelines"]
