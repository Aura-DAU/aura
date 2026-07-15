"""
access_control.py — Full RBAC policy gate (B2-AUTH-4).

Two public surfaces:
  1. resolve_effective_role(identity, db) → str
     Maps the JWT's broad role (student/faculty/admin) to the most elevated
     fine-grained role based on role_bindings. Used by:
       - Pushkar's DLS Qdrant filter (builds the allowed-set from this)
       - AccessControlGate (determines which evaluation path to take)

  2. AccessControlGate.evaluate(identity, query_intent, target_identifier)
     The main per-request authorization decision. Returns AccessResult.

Role hierarchy (fine-grained):
  public < student < faculty_general < faculty_coord < faculty_convenor_ug/pg
                                                      < dean_* (parallel)
                                                      < registrar (parallel)
                                                      < superadmin (top)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── Role allowed-sets for Qdrant DLS filter ───────────────────────────────
# Exported so Pushkar's retrieval_pipeline.py can import and use directly.
ROLE_ALLOWED_SETS: dict[str, set[str]] = {
    "public":              {"public"},
    "student":             {"public", "student"},
    "faculty_general":     {"public", "faculty"},
    "faculty_coord":       {"public", "faculty", "faculty_coord"},
    "faculty_convenor_ug": {"public", "faculty", "faculty_coord", "faculty_convenor_ug"},
    "faculty_convenor_pg": {"public", "faculty", "faculty_coord", "faculty_convenor_pg"},
    "dean_students":       {"public", "student", "faculty", "dean_students"},
    "dean_faculty":        {"public", "faculty", "dean_faculty"},
    "dean_academic":       {"public", "faculty", "faculty_coord",
                            "faculty_convenor_ug", "faculty_convenor_pg", "dean_academic"},
    "registrar":           {"public", "faculty", "dean_academic", "registrar"},
    "admin_staff":         {"public", "student", "faculty", "admin_staff"},
    "superadmin":          set(ROLE_ALLOWED_SETS_PLACEHOLDER := [
                               "public", "student", "faculty", "faculty_coord",
                               "faculty_convenor_ug", "faculty_convenor_pg",
                               "dean_students", "dean_faculty", "dean_academic",
                               "registrar", "admin_staff", "superadmin"]),
}
# Fix the forward-reference placeholder
ROLE_ALLOWED_SETS["superadmin"] = set(ROLE_ALLOWED_SETS_PLACEHOLDER)
del ROLE_ALLOWED_SETS_PLACEHOLDER

# Legacy binding strings → canonical effective role
_LEGACY_MAP = {
    "admin_full":       "superadmin",
    "dean_of_students": "dean_students",
    "exam_committee":   "registrar",
}

# UG and PG program identifier prefixes (extend as needed)
_UG_PREFIXES = ("BTech", "BDes", "BSc", "BSMS", "BTech-")
_PG_PREFIXES = ("MTech", "MSc", "MDes", "MBA", "PhD", "PhD-")


def _is_ug(program_id: str) -> bool:
    return any(program_id.startswith(p) for p in _UG_PREFIXES)

def _is_pg(program_id: str) -> bool:
    return any(program_id.startswith(p) for p in _PG_PREFIXES)


# ── resolve_effective_role ─────────────────────────────────────────────────
def resolve_effective_role(identity, db_module=None) -> str:
    """
    Resolves the JWT's broad role → most elevated fine-grained effective role.

    Called by:
      • retrieval_pipeline.py (Pushkar) to build the Qdrant filter set
      • AccessControlGate to pick the right evaluation path

    Returns one of the keys in ROLE_ALLOWED_SETS.
    """
    if identity.role == "student":
        return "student"

    if db_module is None:
        import db.connection as db_module  # noqa: PLC0415

    bindings = _fetch_bindings(identity.erp_id, db_module)

    # Resolve legacy strings
    bindings = {_LEGACY_MAP.get(b, b) for b in bindings}

    # Check in descending privilege order
    if "superadmin" in bindings:                          return "superadmin"
    if "dean_academic" in bindings:                       return "dean_academic"
    if "dean_students" in bindings:                       return "dean_students"
    if "dean_faculty" in bindings:                        return "dean_faculty"
    if "registrar" in bindings:                           return "registrar"
    if "admin_staff" in bindings:                         return "admin_staff"
    if "faculty_convenor_ug" in bindings:                 return "faculty_convenor_ug"
    if "faculty_convenor_pg" in bindings:                 return "faculty_convenor_pg"
    if any(b.startswith("faculty_coord:") for b in bindings): return "faculty_coord"
    if identity.role == "faculty":                        return "faculty_general"
    if identity.role == "admin":                          return "admin_staff"

    return identity.role


# ── RBAC Gate ──────────────────────────────────────────────────────────────
class AccessDecision(Enum):
    ALLOWED = "allowed"
    DENIED  = "denied"


@dataclass
class AccessResult:
    decision:             AccessDecision
    reason:               str
    allowed_roll_numbers: Optional[list[str]] = None
    scope_type:           Optional[str]       = None   # self|advisee|course|batch|coord|convenor|dean|all
    course_codes:         list[str]           = field(default_factory=list)
    program_id:           Optional[str]       = None   # set for coord/convenor scope
    scope_context:        Optional[str]       = None   # human-readable for audit log


GENERIC_DENIAL = (
    "I'm not able to retrieve that information. "
    "If you believe you should have access to this data, "
    "please contact the Academic Office."
)


def _fetch_bindings(erp_id: str, db) -> set[str]:
    try:
        rows = db.query(
            """SELECT binding FROM role_bindings
               WHERE erp_id = %s
                 AND (expires_at IS NULL OR expires_at > NOW())
                 AND revoked = FALSE""",
            (erp_id,),
        )
        return {r["binding"] for r in rows}
    except Exception:
        return set()


class AccessControlGate:

    def __init__(self, erp_connector, db_module=None):
        self.erp = erp_connector
        if db_module is None:
            import db.connection as db_module  # noqa: PLC0415
        self._db = db_module

    def _get_bindings(self, erp_id: str) -> set[str]:
        raw = _fetch_bindings(erp_id, self._db)
        return {_LEGACY_MAP.get(b, b) for b in raw}

    def evaluate(
        self,
        identity,
        query_intent: dict,
        target_identifier: Optional[str],
    ) -> AccessResult:
        if not identity or not identity.role:
            return AccessResult(AccessDecision.DENIED, "unauthenticated")

        # AGGREGATE — class-level anonymized stats
        if query_intent.get("type") == "AGGREGATE":
            return self._evaluate_aggregate(identity)

        # Own data — always allowed for all roles
        if not target_identifier or target_identifier == identity.erp_id:
            return AccessResult(
                AccessDecision.ALLOWED, "own data",
                allowed_roll_numbers=[identity.erp_id], scope_type="self",
            )

        # Student → another person's data: always denied
        if identity.role == "student":
            return AccessResult(AccessDecision.DENIED, "students may only access their own academic data")

        if identity.role in ("faculty", "admin"):
            return self._evaluate_elevated_access(identity, target_identifier)

        return AccessResult(AccessDecision.DENIED, f"unrecognised role: {identity.role!r}")

    def _evaluate_elevated_access(self, identity, target_identifier: str) -> AccessResult:
        """Handles all faculty and admin sub-roles."""
        bindings = self._get_bindings(identity.erp_id)
        effective = resolve_effective_role(identity, self._db)

        # ── Superadmin / full admin ────────────────────────────────────────
        if effective == "superadmin" or "superadmin" in bindings:
            return AccessResult(AccessDecision.ALLOWED, "superadmin", scope_type="all")

        # ── Dean of Academic / Students / Faculty → any student ───────────
        if effective in ("dean_academic", "dean_students", "dean_faculty") or \
           any(b in bindings for b in ("dean_academic", "dean_students", "dean_faculty")):
            dean_role = effective if effective.startswith("dean") else next(
                b for b in ("dean_academic", "dean_students", "dean_faculty") if b in bindings
            )
            return AccessResult(
                AccessDecision.ALLOWED, f"{dean_role} binding",
                allowed_roll_numbers=[target_identifier],
                scope_type="dean", scope_context=dean_role,
            )

        # ── Registrar / exam committee → any student ───────────────────────
        if effective == "registrar" or "registrar" in bindings:
            return AccessResult(
                AccessDecision.ALLOWED, "registrar binding",
                allowed_roll_numbers=[target_identifier], scope_type="registrar",
            )

        # ── UG Convenor → all UG program students ─────────────────────────
        if effective == "faculty_convenor_ug" or "faculty_convenor_ug" in bindings:
            profile = self.erp.get_student_profile(target_identifier)
            if profile:
                prog = profile.get("program", "")
                if _is_ug(prog):
                    return AccessResult(
                        AccessDecision.ALLOWED, "UG convenor binding",
                        allowed_roll_numbers=[target_identifier],
                        scope_type="convenor", program_id=prog,
                        scope_context=f"UG convenor → {prog}",
                    )

        # ── PG Convenor → all PG program students ─────────────────────────
        if effective == "faculty_convenor_pg" or "faculty_convenor_pg" in bindings:
            profile = self.erp.get_student_profile(target_identifier)
            if profile:
                prog = profile.get("program", "")
                if _is_pg(prog):
                    return AccessResult(
                        AccessDecision.ALLOWED, "PG convenor binding",
                        allowed_roll_numbers=[target_identifier],
                        scope_type="convenor", program_id=prog,
                        scope_context=f"PG convenor → {prog}",
                    )

        # ── Program Coordinator → students in their program ────────────────
        # B2-AUTH-4: binding format is faculty_coord:{program_id}
        for binding in bindings:
            if binding.startswith("faculty_coord:"):
                program_id = binding.split(":", 1)[1]
                if self.erp.student_in_program(target_identifier, program_id):
                    return AccessResult(
                        AccessDecision.ALLOWED,
                        f"program coordinator for {program_id}",
                        allowed_roll_numbers=[target_identifier],
                        scope_type="coord", program_id=program_id,
                        scope_context=f"coordinator:{program_id}",
                    )

        # ── Standard faculty: advisee, shared course, class advisor ─────────
        if self.erp.is_advisee(identity.erp_id, target_identifier):
            return AccessResult(
                AccessDecision.ALLOWED, "student is faculty advisor's advisee",
                allowed_roll_numbers=[target_identifier], scope_type="advisee",
            )

        shared = self.erp.get_shared_courses(identity.erp_id, target_identifier)
        if shared:
            return AccessResult(
                AccessDecision.ALLOWED, f"student in faculty course(s): {shared}",
                allowed_roll_numbers=[target_identifier],
                scope_type="course", course_codes=shared,
            )

        for binding in bindings:
            if binding.startswith("class_advisor:"):
                parts = binding.split(":", 2)
                if len(parts) == 3:
                    _, dept, batch = parts
                    if self.erp.student_in_batch(target_identifier, dept, batch):
                        return AccessResult(
                            AccessDecision.ALLOWED,
                            f"class advisor {dept} batch {batch}",
                            allowed_roll_numbers=[target_identifier],
                            scope_type="batch", scope_context=f"{dept}:{batch}",
                        )

        return AccessResult(
            AccessDecision.DENIED,
            "no advisory, teaching, or administrative relationship with this student",
        )

    def _evaluate_aggregate(self, identity) -> AccessResult:
        """AGGREGATE queries — anonymized class-level stats."""
        if identity.role == "student":
            return AccessResult(AccessDecision.DENIED, "students may not request aggregate statistics")

        bindings  = self._get_bindings(identity.erp_id)
        effective = resolve_effective_role(identity, self._db)

        if effective in ("superadmin", "dean_academic", "dean_students", "registrar") or \
           any(b in bindings for b in ("superadmin", "dean_academic", "admin_full")):
            return AccessResult(AccessDecision.ALLOWED, "elevated binding — aggregate", scope_type="aggregate_all")

        # Convenors: aggregates for all programs in domain
        if effective in ("faculty_convenor_ug", "faculty_convenor_pg"):
            return AccessResult(AccessDecision.ALLOWED, f"{effective} — aggregate", scope_type="aggregate_all")

        # Coordinators: aggregates for their program(s)
        coord_programs = [b.split(":", 1)[1] for b in bindings if b.startswith("faculty_coord:")]
        if coord_programs:
            return AccessResult(
                AccessDecision.ALLOWED, "coordinator aggregate",
                scope_type="aggregate_coord", scope_context=",".join(coord_programs),
            )

        # General faculty: aggregates for their own courses
        courses = self.erp.get_faculty_courses(identity.erp_id)
        if courses:
            return AccessResult(
                AccessDecision.ALLOWED, "faculty aggregate — own courses",
                scope_type="aggregate_course",
                course_codes=[c["course_code"] for c in courses],
            )

        return AccessResult(AccessDecision.DENIED, "no course assignments for aggregate query")
