"""
v7 regression: question quota enforcement (3/day guest, 5/day DAU).

Tests pipeline.rate_limiter directly (the FastAPI /chat endpoint just calls
enforce_quota() and translates QuotaExceeded -> HTTP 429 — see server/api/api.py).
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


def test_quota_is_keyed_per_account_not_shared():
    """Two different guest emails must not share one bucket — this guards
    against accidentally keying by erp_id='GUEST', which every guest shares."""
    enforce_quota("guest-a@gmail.com", "guest")
    enforce_quota("guest-a@gmail.com", "guest")
    # guest-b should still have their full quota
    assert peek_remaining("guest-b@gmail.com", "guest") == 3


def test_peek_remaining_does_not_consume_quota():
    key = "peek-test@dau.ac.in"
    assert peek_remaining(key, "student") == 5
    assert peek_remaining(key, "student") == 5  # calling peek again doesn't decrement
    enforce_quota(key, "student")
    assert peek_remaining(key, "student") == 4
