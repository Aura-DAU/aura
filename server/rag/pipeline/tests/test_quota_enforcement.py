# v8 regression: question quota enforcement — 10/day for anonymous guests
# (no Google sign-in, identified by a cookie-scoped erp_id), unlimited for
# verified @dau.ac.in accounts (student/faculty/admin).

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.rate_limiter import (
    InMemoryQuotaStore,
    enforce_quota,
    peek_remaining,
    QuotaExceeded,
    reset_store_for_tests,
)
import pipeline.rate_limiter as rate_limiter_module


def setup_function(_):
    # Each test gets a clean in-memory store — the module-level singleton
    # would otherwise leak state between tests.
    reset_store_for_tests(InMemoryQuotaStore())
    rate_limiter_module.QUOTA_LIMITS = {
        "guest": 10,
        "student": None,
        "faculty": None,
        "admin": None,
    }


# ── Guest quota tests (limit = 10) ───────────────────────────────────────────

def test_guest_gets_10_questions_then_429():
    key = "GUEST-anon-1"
    for expected_remaining in range(9, -1, -1):
        assert enforce_quota(key, "guest") == expected_remaining
    try:
        enforce_quota(key, "guest")
        assert False, "11th guest question should have raised QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.remaining == 0
        assert exc.limit == 10


def test_guest_gets_429_on_11th_question():
    # Alias test — explicit name mirrors the student equivalent below.
    key = "GUEST-anon-alias"
    for _ in range(10):
        enforce_quota(key, "guest")
    try:
        enforce_quota(key, "guest")
        assert False, "Expected QuotaExceeded"
    except QuotaExceeded as exc:
        assert exc.remaining == 0


# ── DAU account quota tests (unlimited) ──────────────────────────────────────

def test_dau_student_has_unlimited_quota():
    key = "student@dau.ac.in"
    # Well beyond any historical daily limit — never raises, always None.
    for _ in range(50):
        assert enforce_quota(key, "student") is None


def test_dau_faculty_has_unlimited_quota():
    key = "faculty@dau.ac.in"
    for _ in range(50):
        assert enforce_quota(key, "faculty") is None


def test_dau_admin_has_unlimited_quota():
    key = "admin@dau.ac.in"
    for _ in range(50):
        assert enforce_quota(key, "admin") is None


def test_unlimited_roles_never_touch_the_store():
    # Unlimited roles should short-circuit before ever reaching the quota
    # store — a corrupt/unreachable store must not affect DAU accounts.
    key = "student-store-check@dau.ac.in"
    enforce_quota(key, "student")
    assert peek_remaining(key, "student") is None


def test_dau_quota_greater_than_guest_quota():
    # Sanity: unlimited (None) always beats a finite guest quota.
    from pipeline.rate_limiter import QUOTA_LIMITS
    assert QUOTA_LIMITS["student"] is None
    assert isinstance(QUOTA_LIMITS["guest"], int)


# ── Per-account isolation ─────────────────────────────────────────────────────

def test_quota_is_keyed_per_account_not_shared():
    # Two different anonymous guest ids must not share one bucket — this
    # guards against accidentally keying by a fixed erp_id like "GUEST",
    # which every guest would share.
    enforce_quota("GUEST-anon-a", "guest")
    enforce_quota("GUEST-anon-a", "guest")
    # guest-b should still have their full quota
    assert peek_remaining("GUEST-anon-b", "guest") == 10


def test_two_students_have_independent_unlimited_quotas():
    # Even though DAU quota is unlimited, each account is still keyed
    # independently (relevant if the policy is ever tightened again).
    key_a = "student-a@dau.ac.in"
    key_b = "student-b@dau.ac.in"

    for _ in range(20):
        enforce_quota(key_a, "student")

    assert enforce_quota(key_a, "student") is None
    assert peek_remaining(key_b, "student") is None


# ── peek_remaining non-destructive check ─────────────────────────────────────

def test_peek_remaining_does_not_consume_quota():
    key = "peek-test-guest"
    assert peek_remaining(key, "guest") == 10
    assert peek_remaining(key, "guest") == 10  # calling peek again doesn't decrement
    enforce_quota(key, "guest")
    assert peek_remaining(key, "guest") == 9


# ── Wellness guardrail integration ────────────────────────────────────────────
# Confirms the guardrail is importable and returns the correct shape.
# Full classifier tests (LLM path + fallback) live in test_wellness_guardrail.py.

def test_wellness_guardrail_triggers_on_distress_phrase():
    # Keyword fallback must catch an explicit distress phrase.
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    # _fallback_check is tested directly to avoid a live Groq API call in CI.
    assert g._fallback_check("I want to kill myself") is True


def test_wellness_guardrail_passes_on_normal_query():
    # Keyword fallback must not false-positive on a plain academic query.
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    assert g._fallback_check("What is the CGPA cutoff for honours?") is False


def test_wellness_guardrail_response_shape():
    # get_response() must return a non-empty string with key contact info.
    from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
    g = WellnessGuardrail()
    response = g.get_response()
    assert isinstance(response, str)
    assert len(response) > 0
    # Spot-check that DAU-specific contacts are present
    assert "counselling@dau.ac.in" in response
    assert "9152987821" in response  # iCall helpline
