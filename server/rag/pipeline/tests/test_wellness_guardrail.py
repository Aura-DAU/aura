# Tests for the WellnessGuardrail classifier.
# Covers:
# a live Groq API call in CI, matching the project's existing test pattern.

import sys
from pathlib import Path

# Ensure server/rag is on the import path (mirrors conftest.py)
RAG_DIR = Path(__file__).resolve().parent.parent.parent  # server/rag
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
    "I can't take it anymore",
    "I can't go on",
    "I have been self-harming",
    "I cut myself last night",
    "I am hurting myself",
]


@pytest.mark.parametrize("phrase", TRIGGER_PHRASES)
def test_distress_phrase_triggers_guardrail(guardrail, phrase):
    assert guardrail._fallback_check(phrase) is True, (
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
    "I feel like I need to study more",       # "feel" but not distress
    "I don't want to miss this deadline",     # "don't want" but not distress
]


@pytest.mark.parametrize("query", NORMAL_QUERIES)
def test_normal_query_does_not_trigger_guardrail(guardrail, query):
    assert guardrail._fallback_check(query) is False, (
        f"Expected no distress trigger for: {query!r}"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
def test_empty_string_does_not_trigger(guardrail):
    assert guardrail._fallback_check("") is False


def test_whitespace_only_does_not_trigger(guardrail):
    assert guardrail._fallback_check("   ") is False


def test_fallback_check_case_insensitive(guardrail):
    # Pattern matching must be case-insensitive.
    assert guardrail._fallback_check("I WANT TO KILL MYSELF") is True
    assert guardrail._fallback_check("I Want To Kill Myself") is True


def test_fallback_check_embedded_in_sentence(guardrail):
    # Trigger phrase embedded mid-sentence must still fire.
    assert guardrail._fallback_check(
        "Lately I have been thinking I want to end my life because of pressure"
    ) is True


# ---------------------------------------------------------------------------
# Academic-context suppression.
# "can't cope / can't take it / can't go on" is everyday coursework idiom.
# On its own it still routes to the wellness block (see TRIGGER_PHRASES);
# alongside academic framing it must not, or a routine question gets the
# crisis block instead of an answer.
# ---------------------------------------------------------------------------
ACADEMIC_STRESS_QUERIES = [
    "I can't cope with this course load, when is the drop deadline?",
    "I can't take it anymore with this assignment, how do I request an extension?",
    "I can't cope with the exam schedule — what is the re-exam policy?",
    "Can't go on with this elective, how do I withdraw from the course?",
    "I can't take this semester's workload, what is the minimum credit requirement?",
]


@pytest.mark.parametrize("query", ACADEMIC_STRESS_QUERIES)
def test_academic_context_suppresses_ambiguous_phrase(guardrail, query):
    assert guardrail._fallback_check(query) is False, (
        f"Expected no distress trigger for academic query: {query!r}"
    )


UNAMBIGUOUS_WITH_ACADEMIC_CONTEXT = [
    "I want to kill myself over this exam",
    "I failed the course and I want to die",
    "This semester made me suicidal",
    "I have been cutting myself since the assignment deadline",
]


@pytest.mark.parametrize("query", UNAMBIGUOUS_WITH_ACADEMIC_CONTEXT)
def test_academic_context_never_suppresses_explicit_distress(guardrail, query):
    # Suppression applies only to the ambiguous patterns. An explicit statement
    # of self-harm must fire regardless of surrounding coursework wording.
    assert guardrail._fallback_check(query) is True, (
        f"Expected distress trigger despite academic context: {query!r}"
    )


# ---------------------------------------------------------------------------
# Response content
# ---------------------------------------------------------------------------
def test_get_response_is_nonempty_string(guardrail):
    response = guardrail.get_response()
    assert isinstance(response, str)
    assert len(response) > 0


def test_get_response_contains_contact_info(guardrail):
    # Wellness response must contain at least one real contact.
    response = guardrail.get_response()
    assert any(
        contact in response
        for contact in ["counselling@dau.ac.in", "iCall", "9152987821", "AASRA"]
    ), "Wellness response must include at least one contact detail."
