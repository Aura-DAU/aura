"""
Access Control Gate — full RBAC policy (SSO architecture).

Unchanged from the previous version in logic, but updated so _get_bindings()
queries role_bindings.erp_id directly (no UUID user_id join needed since
the users table no longer exists).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AccessDecision(Enum):
    ALLOWED = "allowed"
    DENIED  = "denied"


@dataclass
class AccessResult:
    decision:             AccessDecision
    reason:               str
    allowed_roll_numbers: Optional[list[str]] = None
    scope_type:           Optional[str]       = None
    course_codes:         list[str]           = field(default_factory=list)


GENERIC_DENIAL = (
    "I'm not able to retrieve that information. "
    "If you believe you should have access to this data, "
    "please contact the Academic Office."
)


class AccessControlGate:

    def __init__(self, erp_connector, db_module=None):
        self.erp = erp_connector
        if db_module is None:
            import db.connection as db_module  # noqa: PLC0415
        self._db = db_module

    def evaluate(self, identity, query_intent: dict, target_identifier: Optional[str]) -> AccessResult:
        if not identity or not identity.role:
            return AccessResult(AccessDecision.DENIED, "unauthenticated")

        # AGGREGATE — class-level anonymized stats
        if query_intent.get("type") == "AGGREGATE":
            return self._evaluate_aggregate_access(identity, query_intent)

        # Own data — always allowed
        if not target_identifier or target_identifier == identity.erp_id:
            return AccessResult(
                AccessDecision.ALLOWED, "own data",
                allowed_roll_numbers=[identity.erp_id], scope_type="self",
            )

        # Student → another person's data: never
        if identity.role == "student":
            return AccessResult(AccessDecision.DENIED, "students may only access their own academic data")

        if identity.role == "faculty":
            return self._evaluate_faculty_access(identity, target_identifier)

        if identity.role == "admin":
            bindings = self._get_bindings(identity.erp_id)
            if "admin_full" in bindings:
                return AccessResult(AccessDecision.ALLOWED, "admin_full binding", scope_type="all")
            return AccessResult(AccessDecision.DENIED, "admin account lacks admin_full binding")

        return AccessResult(AccessDecision.DENIED, f"unrecognized role: {identity.role!r}")

    def _evaluate_aggregate_access(self, identity, query_intent: dict) -> AccessResult:
        if identity.role == "student":
            return AccessResult(
                AccessDecision.DENIED,
                "students may not request aggregate class statistics",
            )
        bindings = self._get_bindings(identity.erp_id)
        if "admin_full" in bindings or "dean_of_students" in bindings:
            return AccessResult(AccessDecision.ALLOWED, "elevated binding", scope_type="aggregate_all")
        courses = self.erp.get_faculty_courses(identity.erp_id)
        if courses:
            return AccessResult(
                AccessDecision.ALLOWED, "faculty aggregate — own courses",
                scope_type="aggregate_course",
                course_codes=[c["course_code"] for c in courses],
            )
        return AccessResult(AccessDecision.DENIED, "no active course assignments for aggregate query")

    def _evaluate_faculty_access(self, identity, target_identifier: str) -> AccessResult:
        bindings = self._get_bindings(identity.erp_id)

        if "admin_full" in bindings or "dean_of_students" in bindings:
            return AccessResult(AccessDecision.ALLOWED, "elevated faculty binding", scope_type="all")

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
                            f"class advisor for {dept} batch {batch}",
                            allowed_roll_numbers=[target_identifier], scope_type="batch",
                        )

        return AccessResult(
            AccessDecision.DENIED,
            "faculty has no advisory or teaching relationship with this student",
        )

    def _get_bindings(self, erp_id: str) -> set[str]:
        """Query role_bindings by erp_id directly — no UUID join needed."""
        try:
            rows = self._db.query(
                """SELECT binding FROM role_bindings
                   WHERE erp_id = %s
                     AND (expires_at IS NULL OR expires_at > NOW())
                     AND revoked = FALSE""",
                (erp_id,),
            )
            return {r["binding"] for r in rows}
        except Exception:
            return set()
