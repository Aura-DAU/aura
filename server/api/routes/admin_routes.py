"""
Admin routes — role_bindings management (B2-AUTH-11).

Updated to support scoped binding formats:
  faculty_coord:{program_id}   e.g. faculty_coord:BTech-ICT
  faculty_convenor_ug
  faculty_convenor_pg
  dean_students / dean_faculty / dean_academic
  registrar / admin_staff / superadmin
  class_advisor:{dept}:{batch}  (legacy, still accepted)
  course_instructor:{code}      (legacy, still accepted)

All endpoints require role == 'admin'. A faculty member calling any of these
gets 403 before any DB operation runs.

Example admin workflow:
  1. Appoint a Program Coordinator:
     POST /admin/users/FAC042/bindings
     { "binding": "faculty_coord:BTech-ICT" }

  2. Appoint UG Convenor:
     POST /admin/users/FAC007/bindings
     { "binding": "faculty_convenor_ug" }

  3. Revoke a binding:
     DELETE /admin/bindings/{binding_id}
"""

import re
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

import db.connection as db_conn
from api.auth import require_identity, Identity

router = APIRouter(prefix="/admin", tags=["admin"])

# ── Valid binding patterns ─────────────────────────────────────────────────
# Simple exact-match strings
_EXACT_BINDINGS = {
    "faculty_convenor_ug",
    "faculty_convenor_pg",
    "dean_students",
    "dean_faculty",
    "dean_academic",
    "registrar",
    "admin_staff",
    "superadmin",
    # Legacy equivalents (still stored as-is, access_control maps them)
    "admin_full",
    "dean_of_students",
    "exam_committee",
}

# Regex patterns for parameterised bindings
_PARAM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^faculty_coord:[A-Za-z0-9_\-]+$"),
     "faculty_coord:{program_id}  e.g. faculty_coord:BTech-ICT"),
    (re.compile(r"^class_advisor:[A-Za-z0-9_\-]+:\d{4}$"),
     "class_advisor:{dept}:{batch_year}  e.g. class_advisor:ICT:2024"),
    (re.compile(r"^course_instructor:[A-Z]{2,}\d{3,}$"),
     "course_instructor:{code}  e.g. course_instructor:IT205"),
]


def _validate_binding(binding: str) -> None:
    if binding in _EXACT_BINDINGS:
        return
    for pattern, example in _PARAM_PATTERNS:
        if pattern.match(binding):
            return
    raise HTTPException(
        status_code=400,
        detail=(
            f"Invalid binding string: '{binding}'. "
            "Valid formats: "
            + ", ".join(
                list(_EXACT_BINDINGS)[:5]
            )
            + " ... or parameterised: "
            + " | ".join(ex for _, ex in _PARAM_PATTERNS)
        ),
    )


def _require_admin(identity: Identity = Depends(require_identity)) -> Identity:
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return identity


def _check_erp_exists(erp_id: str) -> None:
    rows = db_conn.query(
        "SELECT 1 FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
        (erp_id,),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No active user with erp_id '{erp_id}' in user_identity_map.",
        )


class AddBindingRequest(BaseModel):
    binding:    str = Field(..., min_length=1, max_length=128)
    expires_at: Optional[str] = Field(None, max_length=64)   # ISO-8601 datetime string, or null = permanent


@router.get("/users/{erp_id}/bindings")
def list_bindings(erp_id: str, admin: Identity = Depends(_require_admin)):
    """List all active and revoked bindings for a user."""
    _check_erp_exists(erp_id)
    rows = db_conn.query(
        """SELECT id, binding, granted_by, granted_at, expires_at, revoked
           FROM role_bindings
           WHERE erp_id = %s
           ORDER BY granted_at DESC""",
        (erp_id,),
    )
    return {"erp_id": erp_id, "bindings": [dict(r) for r in rows]}


@router.post("/users/{erp_id}/bindings")
def add_binding(
    erp_id: str,
    body:   AddBindingRequest,
    admin:  Identity = Depends(_require_admin),
):
    """
    Add a role binding for a user.
    For faculty_coord, supply the program_id:
      { "binding": "faculty_coord:BTech-ICT" }
    For dean roles, just the role string:
      { "binding": "dean_students" }
    """
    binding = body.binding.strip()
    _validate_binding(binding)
    _check_erp_exists(erp_id)

    db_conn.execute(
        """INSERT INTO role_bindings (erp_id, binding, granted_by, expires_at)
           VALUES (%s, %s, %s, %s::timestamptz)""",
        (erp_id, binding, admin.erp_id, body.expires_at),
    )
    return {
        "status":     "added",
        "erp_id":     erp_id,
        "binding":    binding,
        "granted_by": admin.erp_id,
        "expires_at": body.expires_at,
    }


@router.delete("/bindings/{binding_id}")
def revoke_binding(binding_id: str, admin: Identity = Depends(_require_admin)):
    """Revoke an existing binding by its UUID."""
    rows = db_conn.query(
        "SELECT id, erp_id, binding FROM role_bindings WHERE id = %s AND revoked = FALSE",
        (binding_id,),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Binding not found or already revoked.",
        )
    db_conn.execute(
        "UPDATE role_bindings SET revoked = TRUE WHERE id = %s",
        (binding_id,),
    )
    return {
        "status":     "revoked",
        "binding_id": binding_id,
        "erp_id":     rows[0]["erp_id"],
        "binding":    rows[0]["binding"],
    }


@router.get("/programs")
def list_coordinators(admin: Identity = Depends(_require_admin)):
    """List all active program coordinator bindings — useful for admin overview."""
    rows = db_conn.query(
        """SELECT rb.erp_id, rb.binding, rb.granted_at, rb.expires_at,
                  uim.dept
           FROM role_bindings rb
           JOIN user_identity_map uim ON uim.erp_id = rb.erp_id
           WHERE rb.binding LIKE 'faculty_coord:%'
             AND rb.revoked = FALSE
             AND (rb.expires_at IS NULL OR rb.expires_at > NOW())
           ORDER BY rb.binding, rb.erp_id""",
        (),
    )
    return {"coordinators": [dict(r) for r in rows]}


@router.get("/deans")
def list_deans(admin: Identity = Depends(_require_admin)):
    """List all active dean-level and convenor bindings."""
    dean_bindings = [
        "faculty_convenor_ug", "faculty_convenor_pg",
        "dean_students", "dean_faculty", "dean_academic",
        "registrar", "superadmin",
    ]
    # placeholders is built from a hardcoded list — no user input is interpolated.
    placeholders = ",".join(["%s"] * len(dean_bindings))
    query = (
        "SELECT rb.erp_id, rb.binding, rb.granted_at, uim.dept"
        " FROM role_bindings rb"
        " JOIN user_identity_map uim ON uim.erp_id = rb.erp_id"
        " WHERE rb.binding IN (" + placeholders + ")"
        " AND rb.revoked = FALSE"
        " AND (rb.expires_at IS NULL OR rb.expires_at > NOW())"
        " ORDER BY rb.binding, rb.erp_id"
    )
    rows = db_conn.query(query, tuple(dean_bindings))
    return {"dean_bindings": [dict(r) for r in rows]}


@router.get("/latency")
def get_latency_stats(hours: int = 24, admin: Identity = Depends(_require_admin)):
    if hours <= 0 or hours > 720:
        raise HTTPException(
            status_code=400,
            detail="Hours parameter must be between 1 and 720 (30 days)."
        )
    
    rows = db_conn.query(
        """SELECT
            count(*) as count,
            min(guardrail_time) as guardrail_min,
            percentile_cont(0.25) within group (order by guardrail_time) as guardrail_q1,
            percentile_cont(0.50) within group (order by guardrail_time) as guardrail_median,
            percentile_cont(0.75) within group (order by guardrail_time) as guardrail_q3,
            max(guardrail_time) as guardrail_max,
            avg(guardrail_time) as guardrail_mean,
            
            min(retrieval_time) as retrieval_min,
            percentile_cont(0.25) within group (order by retrieval_time) as retrieval_q1,
            percentile_cont(0.50) within group (order by retrieval_time) as retrieval_median,
            percentile_cont(0.75) within group (order by retrieval_time) as retrieval_q3,
            max(retrieval_time) as retrieval_max,
            avg(retrieval_time) as retrieval_mean,
            
            min(generation_time) as generation_min,
            percentile_cont(0.25) within group (order by generation_time) as generation_q1,
            percentile_cont(0.50) within group (order by generation_time) as generation_median,
            percentile_cont(0.75) within group (order by generation_time) as generation_q3,
            max(generation_time) as generation_max,
            avg(generation_time) as generation_mean,
            
            min(total_time) as total_min,
            percentile_cont(0.25) within group (order by total_time) as total_q1,
            percentile_cont(0.50) within group (order by total_time) as total_median,
            percentile_cont(0.75) within group (order by total_time) as total_q3,
            max(total_time) as total_max,
            avg(total_time) as total_mean
        FROM latency_logs
        WHERE created_at >= NOW() - %s * INTERVAL '1 hour'""",
        (hours,)
    )

    if not rows or rows[0]["count"] == 0:
        return {"segments": [], "total_requests": 0}

    r = rows[0]
    count = r["count"]

    segments = []
    for prefix in ["guardrail", "retrieval", "generation", "total"]:
        segments.append({
            "name": prefix,
            "min": r[f"{prefix}_min"],
            "q1": r[f"{prefix}_q1"],
            "median": r[f"{prefix}_median"],
            "q3": r[f"{prefix}_q3"],
            "max": r[f"{prefix}_max"],
            "mean": r[f"{prefix}_mean"],
            "count": count
        })

    return {"segments": segments, "total_requests": count}
