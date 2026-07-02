"""
B7 acceptance tests — all 8 access matrix scenarios.
Updated for SSO architecture: Identity has no user_id UUID — erp_id is
the sole identifier. _get_bindings queries role_bindings.erp_id directly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from unittest.mock import MagicMock
from access_control import AccessControlGate, AccessDecision, GENERIC_DENIAL


class FakeIdentity:
    def __init__(self, erp_id, role, dept=None):
        self.erp_id  = erp_id
        self.role    = role
        self.dept    = dept
        self.user_id = erp_id   # property alias


class FakeERP:
    def __init__(self, is_advisee=False, shared_courses=None, student_in_batch=False, courses=None):
        self._is_advisee     = is_advisee
        self._shared_courses = shared_courses or []
        self._in_batch       = student_in_batch
        self._courses        = courses or []

    def is_advisee(self, f, s):             return self._is_advisee
    def get_shared_courses(self, f, s):     return self._shared_courses
    def student_in_batch(self, s, d, b):    return self._in_batch
    def get_faculty_courses(self, erp_id):  return self._courses


def make_gate(erp, bindings=None):
    mock_db = MagicMock()
    mock_db.query.return_value = [{"binding": b} for b in (bindings or [])]
    return AccessControlGate(erp, db_module=mock_db)


INTENT = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"]}

def test_student_own_data_allowed():
    result = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), INTENT, None)
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "self"

def test_student_other_student_denied():
    result = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), INTENT, "S2")
    assert result.decision == AccessDecision.DENIED

def test_faculty_advisee_allowed():
    result = make_gate(FakeERP(is_advisee=True)).evaluate(FakeIdentity("F1","faculty"), INTENT, "S1")
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "advisee"

def test_faculty_non_advisee_non_enrolled_denied():
    result = make_gate(FakeERP()).evaluate(FakeIdentity("F1","faculty"), INTENT, "S99")
    assert result.decision == AccessDecision.DENIED

def test_faculty_course_student_allowed():
    result = make_gate(FakeERP(shared_courses=["IT205"])).evaluate(FakeIdentity("F1","faculty"), INTENT, "S3")
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "course"
    assert "IT205" in result.course_codes

def test_faculty_class_advisor_binding_allowed():
    result = make_gate(FakeERP(student_in_batch=True), ["class_advisor:ICT:2024"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S5")
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "batch"

def test_faculty_dean_of_students_allowed():
    result = make_gate(FakeERP(), ["dean_of_students"]).evaluate(FakeIdentity("F1","faculty"), INTENT, "S7")
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "all"

def test_admin_full_binding_allowed():
    result = make_gate(FakeERP(), ["admin_full"]).evaluate(FakeIdentity("A1","admin"), INTENT, "S99")
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "all"

def test_admin_without_binding_denied():
    result = make_gate(FakeERP(), []).evaluate(FakeIdentity("A1","admin"), INTENT, "S99")
    assert result.decision == AccessDecision.DENIED

def test_denial_message_is_generic():
    result = make_gate(FakeERP()).evaluate(FakeIdentity("F1","faculty"), INTENT, "S99")
    assert result.decision == AccessDecision.DENIED
    assert "advisor" not in GENERIC_DENIAL and "enrolled" not in GENERIC_DENIAL

def test_unrecognized_role_denied():
    result = make_gate(FakeERP()).evaluate(FakeIdentity("X1","superuser"), INTENT, "S1")
    assert result.decision == AccessDecision.DENIED

def test_faculty_class_advisor_wrong_batch_denied():
    result = make_gate(FakeERP(student_in_batch=False), ["class_advisor:ICT:2024"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S5")
    assert result.decision == AccessDecision.DENIED

def test_aggregate_denied_for_student():
    agg_intent = {"type": "AGGREGATE", "target": None, "erp_fields": ["cgpa"]}
    result = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), agg_intent, None)
    assert result.decision == AccessDecision.DENIED

def test_aggregate_allowed_for_faculty_with_courses():
    agg_intent = {"type": "AGGREGATE", "target": None, "erp_fields": ["attendance"]}
    result = make_gate(FakeERP(courses=[{"course_code":"IT205"}])).evaluate(
        FakeIdentity("F1","faculty"), agg_intent, None)
    assert result.decision == AccessDecision.ALLOWED and result.scope_type == "aggregate_course"
