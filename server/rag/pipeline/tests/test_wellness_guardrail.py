"""
Tests for the WellnessGuardrail classifier.

Covers:
  - Distress phrases that must trigger the guardrail (trigger phrases).
  - Normal university queries that must NOT trigger it (normal queries).
  - Edge cases: empty string, exception safety.
  - Response shape: wellness_response() returns the correct dict keys.
"""

import sys
from pathlib import Path

# Ensure server/rag is on the import path (mirrors conftest.py)
RAG_DIR = Path(__file__).resolve().parent.parent.parent   # server/rag
for p in (str(RAG_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from pipeline.guardrails.wellness_guardrail import WellnessGuardrail


@pytest.fixture
def guardrail():
    return WellnessGuardrail()


# ---------------------------------------------------------------------------
# Distress phrases — must trigger
# ---------------------------------------------------------------------------
TRIGGER_PHRASES = [
    "I want to kill myself",
    "I want to kill my self",
    "I am thinking about suicide",
    "I feel suicidal",
    "I don't want to live anymore",
    "I don't want to be alive",
    "I want to end my life",
    "I want to end it all",
    "I feel completely hopeless",
    "I feel worthless and empty",
    "I feel so numb all the time",
    "I feel broken inside",
    "I feel trapped and helpless",
    "I can't take it anymore",
    "I can't go on",
    "I am falling apart",
    "I am having a mental breakdown",
    "I have been self-harming",
    "I cut myself last night",
    "I am hurting myself",
    "I am being ragged by seniors",
    "I'm experiencing sexual harassment",
    "I need help now",
    "I need emergency help immediately",
    "I am in crisis",
    "I am in danger",
]

@pytest.mark.parametrize("phrase", TRIGGER_PHRASES)
def test_distress_phrase_triggers_guardrail(guardrail, phrase):
    assert guardrail.is_distress(phrase) is True, (
        f"Expected distress trigger for: {phrase!r}"
    )


# ---------------------------------------------------------------------------
# Normal university queries — must NOT trigger
# ---------------------------------------------------------------------------
NORMAL_QUERIES = [
    "What is the CGPA requirement for the honors program?",
    "How do I register for IT301?",
    "When does the semester end?",
    "What clubs are available at DAU?",
    "Who is the dean of students?",
    "How do I apply for the research club?",
    "What is the fee structure for B.Tech ICT?",
    "Can I get a hostel room change?",
    "What are the library timings?",
    "How is CGPA calculated?",
    "I want to join the programming club",
    "Tell me about placement statistics",
    "What is the attendance policy?",
    "How do I appeal my exam result?",
    "I feel like I need to study more",   # "feel" but not distress
    "I don't want to miss this deadline",  # "don't want" but not distress
]

@pytest.mark.parametrize("query", NORMAL_QUERIES)
def test_normal_query_does_not_trigger_guardrail(guardrail, query):
    assert guardrail.is_distress(query) is False, (
        f"Expected no distress trigger for: {query!r}"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_empty_string_does_not_trigger(guardrail):
    assert guardrail.is_distress("") is False


def test_whitespace_only_does_not_trigger(guardrail):
    assert guardrail.is_distress("   ") is False


def test_is_distress_case_insensitive(guardrail):
    """Pattern matching must be case-insensitive."""
    assert guardrail.is_distress("I WANT TO KILL MYSELF") is True
    assert guardrail.is_distress("I Want To Kill Myself") is True


def test_is_distress_embedded_in_sentence(guardrail):
    """Trigger word embedded mid-sentence must still fire."""
    assert guardrail.is_distress(
        "Lately I have been thinking I want to end my life because of pressure"
    ) is True


# ---------------------------------------------------------------------------
# Response shape
# ---------------------------------------------------------------------------
def test_wellness_response_has_required_keys(guardrail):
    resp = guardrail.wellness_response()
    assert "answer" in resp
    assert "sources" in resp
    assert "is_personal_data" in resp
    assert "wellness_escalation" in resp


def test_wellness_response_escalation_flag_is_true(guardrail):
    resp = guardrail.wellness_response()
    assert resp["wellness_escalation"] is True


def test_wellness_response_sources_is_empty_list(guardrail):
    resp = guardrail.wellness_response()
    assert resp["sources"] == []


def test_wellness_response_is_personal_data_is_false(guardrail):
    resp = guardrail.wellness_response()
    assert resp["is_personal_data"] is False


def test_wellness_response_answer_contains_contact_info(guardrail):
    """Wellness response must contain at least one real contact."""
    resp = guardrail.wellness_response()
    answer = resp["answer"]
    assert any(
        contact in answer
        for contact in ["counselling@dau.ac.in", "iCall", "Vandrevala", "9152987821"]
    ), "Wellness response must include at least one contact detail."
