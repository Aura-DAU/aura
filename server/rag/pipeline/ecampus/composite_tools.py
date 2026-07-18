# Composite tools — handlers that combine more than one raw eCampus call (or
# an eCampus call + the RAG knowledge base) into one higher-value answer, so
# questions. Registered in tool_registry.py alongside the single-source tools.

from . import cache
from .client import ECampusClient
from .credentials_vault import (
    CredentialsNotLinked,
    has_advisor_consent,
    grant_advisor_consent,
    revoke_advisor_consent,
    list_consented_faculty,
)
from ..personal_data.access_control import authorize_personal_query, AccessDenied
from ..personal_data.audit import audit_log

DEFAULT_ATTENDANCE_THRESHOLD = 75.0  # fallback only — prefer the RAG-sourced value below


def _own_client(identity) -> ECampusClient:
    # Raises AccessDenied (identity) or CredentialsNotLinked (vault) —
    # callers must handle both.
    student_id = authorize_personal_query(identity, target_student_id=None)
    return ECampusClient(erp_id=student_id)


def _attendance_threshold() -> float:
    # Pulls the real attendance-eligibility threshold from the indexed
    # Academic Handbook rather than hardcoding it, since policy doc text is
    # the authoritative source and can change between catalog years.
    try:
        from ..retrieval.retrieval_pipeline import RetrievalPipeline
        import re
        result = RetrievalPipeline().get_context("minimum attendance percentage examination eligibility")
        match = re.search(r"(\d{2})\s*%", result.get("context", ""))
        if match:
            return float(match.group(1))
    except Exception:
        # Fallback to default threshold if handbook retrieval fails
        pass
    return DEFAULT_ATTENDANCE_THRESHOLD


# ── check_exam_eligibility ──────────────────────────────────────────────
def check_exam_eligibility(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
        attendance = client.get_attendance()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}

    threshold = _attendance_threshold()
    at_risk = []
    for course in attendance:
        try:
            pct = float(str(course.get("percentage", "0")).replace("%", ""))
        except ValueError:
            continue
        if pct < threshold:
            at_risk.append({**course, "threshold": threshold})

    audit_log(identity, query="check_exam_eligibility", allowed=True, target=client.erp_id)
    return {
        "threshold_used": threshold,
        "at_risk_courses": at_risk,
        "eligible_for_all_exams": len(at_risk) == 0,
        "note": "Threshold sourced from the Academic Handbook where available; verify against the official policy for edge cases (medical exemptions, etc.) rather than treating this as final.",
    }


# ── get_academic_snapshot ───────────────────────────────────────────────
def get_academic_snapshot(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}
    snapshot = {}
    errors = {}
    for key, fn in [
        ("cgpa", client.get_cgpa),
        ("attendance", client.get_attendance),
        ("fees", client.get_fees),
        ("hostel", client.get_hostel),
        ("registration", client.get_registration),
    ]:
        try:
            snapshot[key] = fn()
        except Exception as e:
            errors[key] = str(e)

    audit_log(identity, query="get_academic_snapshot", allowed=True, target=client.erp_id)
    if errors:
        snapshot["_partial_errors"] = errors
    return snapshot


# ── compare_semester_trend ──────────────────────────────────────────────
def compare_semester_trend(identity, **kwargs) -> dict:
    try:
        client = _own_client(identity)
        result = client.get_result()
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "link_ecampus_account"}

    by_semester: dict[str, list] = {}
    for g in result.get("grades", []):
        by_semester.setdefault(g.get("semester", "unknown"), []).append(g)

    audit_log(identity, query="compare_semester_trend", allowed=True, target=client.erp_id)
    return {
        "semesters_seen": sorted(by_semester.keys()),
        "courses_per_semester": {sem: len(courses) for sem, courses in by_semester.items()},
        "note": "SGPA-level numeric trend requires parsers.parse_result's TODOs to be filled in with real per-semester SGPA values — this returns the grade breakdown available today.",
    }


# ── refresh_my_data ──────────────────────────────────────────────────────
def refresh_my_data(identity, **kwargs) -> dict:
    student_id = authorize_personal_query(identity, target_student_id=None)
    cache.invalidate(student_id)
    audit_log(identity, query="refresh_my_data", allowed=True, target=student_id)
    return {"status": "cache cleared — next request will re-fetch from eCampus"}


# ── share_data_with_advisor / revoke_advisor_access ───────────────────────
def share_data_with_advisor(identity, faculty_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can grant advisor data-sharing consent.")
    grant_advisor_consent(identity["erp_id"], faculty_erp_id)
    audit_log(identity, query="share_data_with_advisor", allowed=True, target=faculty_erp_id)
    return {"status": "shared", "faculty_erp_id": faculty_erp_id}


def revoke_advisor_access(identity, faculty_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can revoke advisor data-sharing consent.")
    revoke_advisor_consent(identity["erp_id"], faculty_erp_id)
    audit_log(identity, query="revoke_advisor_access", allowed=True, target=faculty_erp_id)
    return {"status": "revoked", "faculty_erp_id": faculty_erp_id}


def list_my_data_sharing(identity, **kwargs) -> dict:
    if identity["role"] != "student":
        raise AccessDenied("Only students can view their own data-sharing settings.")
    return {"shared_with": list_consented_faculty(identity["erp_id"])}


# ── get_advisee_snapshot (faculty, consent-gated) ──────────────────────
def get_advisee_snapshot(identity, student_erp_id: str, **kwargs) -> dict:
    if identity["role"] != "faculty":
        raise AccessDenied("Only faculty may request an advisee's academic snapshot.")

    # Consent check FIRST, before the generic role-based check — a faculty
    # member being a real advisor in eCampus is not sufficient on its own
    # under the credential-vault model (see access_control.py's note).
    if not has_advisor_consent(student_erp_id, identity["erp_id"]):
        audit_log(identity, query="get_advisee_snapshot", allowed=False, target=student_erp_id,
                   reason="Student has not shared data with this faculty member.")
        return {
            "error": "This student hasn't shared their academic data with you through AURA.",
            "action_needed": "student_consent_required",
        }

    target_id = authorize_personal_query(identity, target_student_id=student_erp_id)
    client = ECampusClient(erp_id=target_id)
    try:
        snapshot = {
            "cgpa": client.get_cgpa(),
            "attendance": client.get_attendance(),
        }
    except CredentialsNotLinked as e:
        return {"error": str(e), "action_needed": "student_has_not_linked_ecampus"}

    audit_log(identity, query="get_advisee_snapshot", allowed=True, target=target_id)
    return snapshot
