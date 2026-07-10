"""
v7 regression: question quota enforcement (3/day guest, 5/day DAU).

Tests pipeline.rate_limiter directly (the FastAPI /chat endpoint just calls
enforce_quota() and translates QuotaExceeded -> HTTP 429 — see server/api/api.py).

Wellness guardrail integration tests are at the bottom of this file.
They confirm the guardrail is importable from within the test environment
and returns the correct shape. Full guardrail tests live in
test_wellness_guardrail.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.rate_limiter import (
    InMemoryQuotaStore,
    enforce_quota,
    peek_remaining,
    QuotaExceeded,
)
import pipeline.rate_limiter as rate_limiter_module


def setup_function(_):
    # Each test gets a clean in-memory store — the module-level singleton
    # would otherwise leak state between tests.
    rate_limiter_module._store = InMemoryQuotaStore()


# ── Guest quota tests (limit = 3) ────────────────────────────────────────────

def test_guest_gets_3_questions_then_429():
    key = "guest-user@gmail.com"
    assert enforce_quota(key, "guest") == 2
    assert enforce_quota(key, "guest") == 1
    assert enforce_quota(key, "guest") == 0
    try:
        enforce_quota(key, "guest")
        assert False, "4th guest question should have raised QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.remaining == 0
        assert exc.limit == 3


def test_guest_gets_429_on_4th_question():
    """Alias test — explicit name mirrors the student equivalent below."""
    key = "guest-alias@gmail.com"
    for _ in range(3):
        enforce_quota(key, "guest")
    try:
        enforce_quota(key, "guest")
        assert False, "Expected QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.remaining == 0


# ── Student quota tests (limit = 5) ──────────────────────────────────────────

def test_dau_student_gets_5_questions_then_429():
    key = "student@dau.ac.in"
    for expected_remaining in (4, 3, 2, 1, 0):
        assert enforce_quota(key, "student") == expected_remaining
    try:
        enforce_quota(key, "student")
        assert False, "6th student question should have raised QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.remaining == 0
        assert exc.limit == 5


def test_student_429_exception_has_detail():
    """QuotaExceeded carries both remaining and limit for the 429 response body."""
    key = "detail-check@dau.ac.in"
    for _ in range(5):
        enforce_quota(key, "student")
    try:
        enforce_quota(key, "student")
        assert False, "Expected QuotaExceeded"
    except QuotaExceeded as exc:
        assert hasattr(exc, "remaining")
        assert hasattr(exc, "limit")


def test_student_limit_greater_than_guest_limit():
    """Sanity: DAU students (5) always get more questions than guests (3)."""
    from pipeline.rate_limiter import STUDENT_DAILY_LIMIT, GUEST_DAILY_LIMIT
    assert STUDENT_DAILY_LIMIT > GUEST_DAILY_LIMIT


# ── Per-account isolation ─────────────────────────────────────────────────────

def test_quota_is_keyed_per_account_not_shared():
    """Two different guest emails must not share one bucket — this guards
    against accidentally keying by erp_id='GUEST', which every guest shares."""
    enforce_quota("guest-a@gmail.com", "guest")
    enforce_quota("guest-a@gmail.com", "guest")
    # guest-b should still have their full quota
    assert peek_remaining("guest-b@gmail.com", "guest") == 3


def test_two_students_have_independent_quotas():
    """Exhausting one student's quota must not affect another student."""
    key_a = "student-a@dau.ac.in"
    key_b = "student-b@dau.ac.in"

    # Exhaust student A
    for _ in range(5):
        enforce_quota(key_a, "student")

    # A is now rate-limited
    try:
        enforce_quota(key_a, "student")
        assert False, "Expected QuotaExceeded for student A"
    except QuotaExceeded:
        pass

    # B still has their full quota
    assert peek_remaining(key_b, "student") == 5


# ── peek_remaining non-destructive check ─────────────────────────────────────

def test_peek_remaining_does_not_consume_quota():
    key = "peek-test@dau.ac.in"
    assert peek_remaining(key, "student") == 5
    assert peek_remaining(key, "student") == 5  # calling peek again doesn't decrement
    enforce_quota(key, "student")
    assert peek_remaining(key, "student") == 4


# ── Wellness guardrail integration ────────────────────────────────────────────
# Confirms the guardrail is importable and returns the correct shape.
# Full classifier tests (LLM path + fallback) live in test_wellness_guardrail.py.

def test_wellness_guardrail_triggers_on_distress_phrase():
    """Keyword fallback must catch an explicit distress phrase."""
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    # _fallback_check is tested directly to avoid a live Groq API call in CI.
    assert g._fallback_check("I want to kill myself") is True


def test_wellness_guardrail_passes_on_normal_query():
    """Keyword fallback must not false-positive on a plain academic query."""
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    assert g._fallback_check("What is the CGPA cutoff for honours?") is False


def test_wellness_guardrail_response_shape():
    """get_response() must return a non-empty string with key contact info."""
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    response = g.get_response()
    assert isinstance(response, str)
    assert len(response) > 0
    # Spot-check that DAU-specific contacts are present
    assert "counselling@dau.ac.in" in response
    assert "9152987821" in response  # iCall helpline