"""
B2-AUTH-10: Access gate tests — all original 8 scenarios + new
coordinator / convenor / dean / registrar / superadmin scenarios.

Uses FakeIdentity (no DB UUID) and FakeERP (controls all relationship
answers) so tests run without any real DB or ERP.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import MagicMock
from access_control import AccessControlGate, AccessDecision, GENERIC_DENIAL


# ── Fakes ──────────────────────────────────────────────────────────────────
class FakeIdentity:
    def __init__(self, erp_id, role, dept=None):
        self.erp_id  = erp_id
        self.role    = role
        self.dept    = dept
        self.user_id = erp_id  # backward-compat property


class FakeERP:
    def __init__(
        self,
        is_advisee=False,
        shared_courses=None,
        student_in_batch=False,
        student_in_program=None,   # dict: {student_id: program_id}
        student_profile=None,      # dict: {student_id: {"program": "BTech-ICT"}}
        courses=None,
    ):
        self._is_advisee        = is_advisee
        self._shared_courses    = shared_courses or []
        self._in_batch          = student_in_batch
        self._in_program        = student_in_program or {}
        self._student_profile   = student_profile or {}
        self._courses           = courses or []

    def is_advisee(self, f, s):                  return self._is_advisee
    def get_shared_courses(self, f, s):          return self._shared_courses
    def student_in_batch(self, s, d, b):         return self._in_batch
    def student_in_program(self, s, pid):
        return self._in_program.get(s) == pid
    def get_student_profile(self, s):
        return self._student_profile.get(s)
    def get_faculty_courses(self, erp_id):       return self._courses


def make_gate(erp, bindings=None):
    mock_db = MagicMock()
    mock_db.query.return_value = [{"binding": b} for b in (bindings or [])]
    return AccessControlGate(erp, db_module=mock_db)


INTENT = {"type": "PERSONAL", "target": "self", "erp_fields": ["cgpa"]}
AGG    = {"type": "AGGREGATE", "target": None, "erp_fields": ["cgpa"]}


# ══════════════════════════════════════════════════════════════════════════
# ORIGINAL 8 SCENARIOS (unchanged)
# ══════════════════════════════════════════════════════════════════════════

def test_1_student_own_data_allowed():
    r = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), INTENT, None)
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "self"

def test_2_student_other_student_denied():
    r = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), INTENT, "S2")
    assert r.decision == AccessDecision.DENIED

def test_3_faculty_advisee_allowed():
    r = make_gate(FakeERP(is_advisee=True)).evaluate(FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "advisee"

def test_4_faculty_non_advisee_non_enrolled_denied():
    r = make_gate(FakeERP()).evaluate(FakeIdentity("F1","faculty"), INTENT, "S99")
    assert r.decision == AccessDecision.DENIED

def test_5_faculty_course_student_allowed():
    r = make_gate(FakeERP(shared_courses=["IT205"])).evaluate(FakeIdentity("F1","faculty"), INTENT, "S3")
    assert r.decision == AccessDecision.ALLOWED
    assert r.scope_type == "course" and "IT205" in r.course_codes

def test_6_faculty_class_advisor_binding_allowed():
    r = make_gate(
        FakeERP(student_in_batch=True),
        ["class_advisor:ICT:2024"]
    ).evaluate(FakeIdentity("F1","faculty"), INTENT, "S5")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "batch"

def test_7_faculty_dean_of_students_binding_allowed():
    r = make_gate(FakeERP(), ["dean_students"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S7")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "dean"

def test_8_admin_full_binding_allowed():
    r = make_gate(FakeERP(), ["superadmin"]).evaluate(
        FakeIdentity("A1","admin"), INTENT, "S99")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "all"


# ══════════════════════════════════════════════════════════════════════════
# NEW: PROGRAM COORDINATOR SCENARIOS
# ══════════════════════════════════════════════════════════════════════════

def test_coord_can_access_student_in_own_program():
    erp = FakeERP(student_in_program={"S1": "BTech-ICT"})
    r   = make_gate(erp, ["faculty_coord:BTech-ICT"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED
    assert r.scope_type == "coord"
    assert r.program_id == "BTech-ICT"

def test_coord_cannot_access_student_in_different_program():
    erp = FakeERP(student_in_program={"S1": "MTech-ICT"})   # different from coord's program
    r   = make_gate(erp, ["faculty_coord:BTech-ICT"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.DENIED

def test_coord_with_multiple_programs_allowed_for_either():
    erp = FakeERP(student_in_program={"S1": "BTech-ECE"})
    r   = make_gate(erp, ["faculty_coord:BTech-ICT", "faculty_coord:BTech-ECE"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED and r.program_id == "BTech-ECE"

def test_coord_scope_context_is_populated():
    erp = FakeERP(student_in_program={"S1": "BTech-ICT"})
    r   = make_gate(erp, ["faculty_coord:BTech-ICT"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.scope_context is not None and "BTech-ICT" in r.scope_context

def test_coord_aggregate_allowed_for_own_program():
    r = make_gate(FakeERP(), ["faculty_coord:BTech-ICT"]).evaluate(
        FakeIdentity("F1","faculty"), AGG, None)
    assert r.decision == AccessDecision.ALLOWED and "coord" in (r.scope_type or "")


# ══════════════════════════════════════════════════════════════════════════
# NEW: UG / PG CONVENOR SCENARIOS
# ══════════════════════════════════════════════════════════════════════════

def test_ug_convenor_can_access_ug_student():
    erp = FakeERP(student_profile={"S1": {"program": "BTech-ICT"}})
    r   = make_gate(erp, ["faculty_convenor_ug"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "convenor"

def test_ug_convenor_cannot_access_pg_student():
    erp = FakeERP(student_profile={"S1": {"program": "MTech-ICT"}})
    r   = make_gate(erp, ["faculty_convenor_ug"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    # MTech is PG — UG convenor should not have access; falls through to standard checks
    assert r.decision == AccessDecision.DENIED

def test_pg_convenor_can_access_pg_student():
    erp = FakeERP(student_profile={"S1": {"program": "MTech-ICT"}})
    r   = make_gate(erp, ["faculty_convenor_pg"]).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "convenor"

def test_convenor_aggregate_allowed():
    r = make_gate(FakeERP(), ["faculty_convenor_ug"]).evaluate(
        FakeIdentity("F1","faculty"), AGG, None)
    assert r.decision == AccessDecision.ALLOWED


# ══════════════════════════════════════════════════════════════════════════
# NEW: DEAN SCENARIOS
# ══════════════════════════════════════════════════════════════════════════

def test_dean_students_can_access_any_student():
    r = make_gate(FakeERP(), ["dean_students"]).evaluate(
        FakeIdentity("D1","faculty"), INTENT, "S_any")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "dean"

def test_dean_academic_can_access_any_student():
    r = make_gate(FakeERP(), ["dean_academic"]).evaluate(
        FakeIdentity("D2","faculty"), INTENT, "S_any")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "dean"

def test_dean_faculty_can_access_any_student():
    r = make_gate(FakeERP(), ["dean_faculty"]).evaluate(
        FakeIdentity("D3","faculty"), INTENT, "S_any")
    assert r.decision == AccessDecision.ALLOWED

def test_dean_students_aggregate_allowed():
    r = make_gate(FakeERP(), ["dean_students"]).evaluate(
        FakeIdentity("D1","faculty"), AGG, None)
    assert r.decision == AccessDecision.ALLOWED

def test_dean_scope_context_is_populated():
    r = make_gate(FakeERP(), ["dean_students"]).evaluate(
        FakeIdentity("D1","faculty"), INTENT, "S1")
    assert r.scope_context is not None


# ══════════════════════════════════════════════════════════════════════════
# NEW: REGISTRAR / SUPERADMIN SCENARIOS
# ══════════════════════════════════════════════════════════════════════════

def test_registrar_can_access_any_student():
    r = make_gate(FakeERP(), ["registrar"]).evaluate(
        FakeIdentity("R1","admin"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "registrar"

def test_superadmin_can_access_any_student():
    r = make_gate(FakeERP(), ["superadmin"]).evaluate(
        FakeIdentity("IT1","admin"), INTENT, "S99")
    assert r.decision == AccessDecision.ALLOWED and r.scope_type == "all"

def test_admin_role_without_binding_denied():
    r = make_gate(FakeERP(), []).evaluate(
        FakeIdentity("A1","admin"), INTENT, "S99")
    assert r.decision == AccessDecision.DENIED


# ══════════════════════════════════════════════════════════════════════════
# SECURITY REGRESSION TESTS
# ══════════════════════════════════════════════════════════════════════════

def test_generic_denial_message_reveals_no_relationship_info():
    assert "advisor" not in GENERIC_DENIAL
    assert "enrolled" not in GENERIC_DENIAL
    assert "program" not in GENERIC_DENIAL
    assert "coordinator" not in GENERIC_DENIAL

def test_student_cannot_get_aggregate():
    r = make_gate(FakeERP()).evaluate(FakeIdentity("S1","student"), AGG, None)
    assert r.decision == AccessDecision.DENIED

def test_unrecognised_role_denied():
    r = make_gate(FakeERP()).evaluate(FakeIdentity("X1","superuser"), INTENT, "S1")
    assert r.decision == AccessDecision.DENIED

def test_legacy_admin_full_maps_to_superadmin():
    r = make_gate(FakeERP(), ["admin_full"]).evaluate(
        FakeIdentity("A1","admin"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED

def test_legacy_dean_of_students_maps_correctly():
    r = make_gate(FakeERP(), ["dean_of_students"]).evaluate(
        FakeIdentity("D1","faculty"), INTENT, "S1")
    assert r.decision == AccessDecision.ALLOWED

def test_faculty_without_any_binding_denied_for_unrelated_student():
    r = make_gate(FakeERP(is_advisee=False, shared_courses=[])).evaluate(
        FakeIdentity("F1","faculty"), INTENT, "S99")
    assert r.decision == AccessDecision.DENIED

def test_faculty_general_aggregate_allowed_with_courses():
    r = make_gate(FakeERP(courses=[{"course_code":"IT205"}])).evaluate(
        FakeIdentity("F1","faculty"), AGG, None)
    assert r.decision == AccessDecision.ALLOWED

def test_faculty_general_aggregate_denied_without_courses():
    r = make_gate(FakeERP(courses=[])).evaluate(
        FakeIdentity("F1","faculty"), AGG, None)
    assert r.decision == AccessDecision.DENIED

def test_own_data_always_allowed_regardless_of_role():
    """Every role can always access their own data."""
    for role in ("student", "faculty", "admin"):
        r = make_gate(FakeERP()).evaluate(
            FakeIdentity("X1", role), INTENT, None)
        assert r.decision == AccessDecision.ALLOWED, f"Failed for role: {role}"
        assert r.scope_type == "self"