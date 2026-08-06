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
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

import db.connection as db_conn
from api.auth import require_identity, Identity
from access_control import resolve_effective_role

router = APIRouter(prefix="/admin", tags=["admin"])

_DAU_EMAIL_DOMAIN = "dau.ac.in"
_STUDENT_ERP_PATTERN = re.compile(r"^\d{9}$")
_ADMIN_STAFF_BINDING = "admin_staff"

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


ADMIN_LEVEL_ROLES = {"admin_staff", "superadmin"}


def _require_admin(identity: Identity = Depends(require_identity)) -> Identity:
    # SEC-08 fix: previously checked only identity.role != "admin", which
    # ignores the fine-grained role_bindings system entirely — a faculty
    # member whose JWT carries role="faculty" but who has an admin_staff or
    # superadmin binding (the RBAC system's actual source of truth for
    # elevated access) was incorrectly locked out of every admin endpoint.
    effective_role = resolve_effective_role(identity)
    if effective_role not in ADMIN_LEVEL_ROLES:
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


class GrantDashboardAccessRequest(BaseModel):
    email:  str = Field(..., min_length=5, max_length=320)
    role:   Literal["admin"] = "admin"
    erp_id: Optional[str] = Field(None, min_length=1, max_length=64)
    dept:   Optional[str] = Field(None, max_length=64)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RevokeDashboardAccessRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=320)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        return value.strip().lower()


def _validate_dau_email(email: str) -> None:
    if "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address.")
    local, domain = email.rsplit("@", 1)
    if not local or domain != _DAU_EMAIL_DOMAIN:
        raise HTTPException(
            status_code=400,
            detail=f"Email must be an @{_DAU_EMAIL_DOMAIN} address.",
        )


def _resolve_erp_id(email: str, erp_id: Optional[str]) -> str:
    if erp_id:
        erp_id = erp_id.strip()
        if not erp_id:
            raise HTTPException(status_code=400, detail="erp_id cannot be empty.")
        return erp_id

    local = email.split("@", 1)[0]
    if _STUDENT_ERP_PATTERN.match(local):
        return local

    raise HTTPException(
        status_code=400,
        detail=(
            "erp_id is required when the email local-part is not a 9-digit student ID."
        ),
    )


def _infer_base_role(erp_id: str) -> Literal["student", "faculty"]:
    """Map an erp_id back to student/faculty after admin dashboard access is revoked.

    user_identity_map only stores student|faculty|admin. 9-digit IDs are students;
    everything else (FAC…, staff codes) is treated as faculty.
    """
    if _STUDENT_ERP_PATTERN.match(erp_id):
        return "student"
    return "faculty"


def _ensure_admin_staff_binding(erp_id: str, granted_by: str) -> bool:
    rows = db_conn.query(
        """SELECT id FROM role_bindings
           WHERE erp_id = %s AND binding = %s AND revoked = FALSE
             AND (expires_at IS NULL OR expires_at > NOW())""",
        (erp_id, _ADMIN_STAFF_BINDING),
    )
    if rows:
        return False

    db_conn.execute(
        """INSERT INTO role_bindings (erp_id, binding, granted_by, expires_at)
           VALUES (%s, %s, %s, NULL)""",
        (erp_id, _ADMIN_STAFF_BINDING, granted_by),
    )
    return True


def _revoke_admin_staff_bindings(erp_id: str) -> int:
    rows = db_conn.query(
        """SELECT id FROM role_bindings
           WHERE erp_id = %s AND binding = %s AND revoked = FALSE""",
        (erp_id, _ADMIN_STAFF_BINDING),
    )
    if not rows:
        return 0

    db_conn.execute(
        """UPDATE role_bindings SET revoked = TRUE
           WHERE erp_id = %s AND binding = %s AND revoked = FALSE""",
        (erp_id, _ADMIN_STAFF_BINDING),
    )
    return len(rows)


@router.get("/users/access")
def list_dashboard_access(admin: Identity = Depends(_require_admin)):
    """List active dashboard admin users (user_identity_map.role = admin)."""
    rows = db_conn.query(
        """SELECT uim.email, uim.erp_id, uim.dept, uim.created_at,
                  EXISTS (
                    SELECT 1 FROM role_bindings rb
                    WHERE rb.erp_id = uim.erp_id
                      AND rb.binding = %s
                      AND rb.revoked = FALSE
                      AND (rb.expires_at IS NULL OR rb.expires_at > NOW())
                  ) AS has_admin_staff_binding
           FROM user_identity_map uim
           WHERE uim.role = 'admin' AND uim.is_active = TRUE
           ORDER BY uim.email""",
        (_ADMIN_STAFF_BINDING,),
    )
    return {
        "admins": [
            {
                "email": r["email"],
                "erp_id": r["erp_id"],
                "dept": r.get("dept"),
                "created_at": r.get("created_at"),
                "has_admin_staff_binding": bool(r["has_admin_staff_binding"]),
            }
            for r in rows
        ],
    }


@router.post("/users/access")
def grant_dashboard_access(
    body: GrantDashboardAccessRequest,
    admin: Identity = Depends(_require_admin),
):
    """Grant admin dashboard access by email (upserts user_identity_map + admin_staff binding)."""
    _validate_dau_email(body.email)
    erp_id = _resolve_erp_id(body.email, body.erp_id)

    existing = db_conn.query(
        "SELECT erp_id, email FROM user_identity_map WHERE email = %s OR erp_id = %s",
        (body.email, erp_id),
    )
    if existing:
        row = existing[0]
        if row["email"] != body.email:
            raise HTTPException(
                status_code=409,
                detail=f"erp_id '{erp_id}' is already assigned to another email.",
            )
        if row["erp_id"] != erp_id:
            raise HTTPException(
                status_code=409,
                detail=f"Email '{body.email}' is already mapped to erp_id '{row['erp_id']}'.",
            )

    db_conn.execute(
        """INSERT INTO user_identity_map (email, erp_id, role, dept, is_active)
           VALUES (%s, %s, %s, %s, TRUE)
           ON CONFLICT (email) DO UPDATE
           SET erp_id = EXCLUDED.erp_id,
               role = EXCLUDED.role,
               dept = COALESCE(EXCLUDED.dept, user_identity_map.dept),
               is_active = TRUE""",
        (body.email, erp_id, body.role, body.dept),
    )

    binding_added = _ensure_admin_staff_binding(erp_id, admin.erp_id)

    return {
        "status": "granted",
        "email": body.email,
        "erp_id": erp_id,
        "role": body.role,
        "admin_staff_binding_added": binding_added,
        "granted_by": admin.erp_id,
    }


@router.delete("/users/access")
def revoke_dashboard_access(
    body: RevokeDashboardAccessRequest,
    admin: Identity = Depends(_require_admin),
):
    """Revoke dashboard admin access: demote role to student/faculty, revoke admin_staff bindings.

    Keeps the account active so SSO login continues to work.
    """
    _validate_dau_email(body.email)

    rows = db_conn.query(
        "SELECT erp_id, role, is_active FROM user_identity_map WHERE email = %s",
        (body.email,),
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No user found for email '{body.email}'.",
        )

    target = rows[0]
    if target["role"] != "admin":
        raise HTTPException(
            status_code=400,
            detail=f"User '{body.email}' does not have admin dashboard access.",
        )

    if target["erp_id"] == admin.erp_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot revoke your own admin dashboard access.",
        )

    # Demote to student/faculty and keep the account active. Setting is_active=FALSE
    # would ban the user from SSO entirely (/internal/resolve-identity requires
    # is_active=TRUE) — revoke must only remove dashboard admin access.
    restored_role = _infer_base_role(target["erp_id"])
    db_conn.execute(
        """UPDATE user_identity_map
           SET role = %s, is_active = TRUE
           WHERE email = %s""",
        (restored_role, body.email),
    )
    bindings_revoked = _revoke_admin_staff_bindings(target["erp_id"])

    return {
        "status": "revoked",
        "email": body.email,
        "erp_id": target["erp_id"],
        "restored_role": restored_role,
        "bindings_revoked": bindings_revoked,
        "revoked_by": admin.erp_id,
    }


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
    placeholders = ",".join(["%s"] * len(dean_bindings))
    rows = db_conn.query(
        f"""SELECT rb.erp_id, rb.binding, rb.granted_at,
                   uim.dept
            FROM role_bindings rb
            JOIN user_identity_map uim ON uim.erp_id = rb.erp_id
            WHERE rb.binding IN ({placeholders})
              AND rb.revoked = FALSE
              AND (rb.expires_at IS NULL OR rb.expires_at > NOW())
            ORDER BY rb.binding, rb.erp_id""",
        tuple(dean_bindings),
    )
    return {"dean_bindings": [dict(r) for r in rows]}


@router.get("/stats/users")
def get_user_stats(days: int = 7, admin: Identity = Depends(_require_admin)):
    """
    User counts for the admin dashboard, split by role.

    registered       — active accounts in user_identity_map (is_active = TRUE)
    recently_active  — distinct users seen in audit_log within the window.
                       audit_log only records personal-data queries, so this
                       undercounts users who exclusively ask public questions.
    """
    if days <= 0 or days > 90:
        raise HTTPException(
            status_code=400,
            detail="Days parameter must be between 1 and 90.",
        )

    registered_rows = db_conn.query(
        """SELECT role, COUNT(*) AS count
           FROM user_identity_map
           WHERE is_active = TRUE
           GROUP BY role""",
        (),
    )
    active_rows = db_conn.query(
        """SELECT role, COUNT(DISTINCT erp_id) AS count
           FROM audit_log
           WHERE ts >= NOW() - %s * INTERVAL '1 day'
           GROUP BY role""",
        (days,),
    )

    def _by_role(rows) -> dict:
        counts = {"student": 0, "faculty": 0, "admin": 0}
        for r in rows:
            if r["role"] in counts:
                counts[r["role"]] = r["count"]
        counts["total"] = sum(counts.values())
        return counts

    return {
        "registered": _by_role(registered_rows),
        "recently_active": _by_role(active_rows),
        "window_days": days,
    }


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
