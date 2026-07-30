# auth.py — FastAPI identity middleware (SSO / Next.js JWT architecture).

# FastAPI never issues tokens. It only verifies the short-lived internal JWT
# that Next.js mints after Google SSO, then attaches to every request.

# JWT claim shape (minted by Next.js):
#   { erpId, role, department, exp }
#   role is the BROAD role from user_identity_map: student | faculty | admin
#   Fine-grained roles (faculty_coord, dean_students, etc.) are resolved
#   server-side via role_bindings — see access_control.resolve_effective_role()

import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

def get_internal_jwt_secret() -> str:
    """Return INTERNAL_JWT_SECRET, or empty string if unset.

    Callers must treat an empty return as misconfiguration (HTTP 500).
    Tests set INTERNAL_JWT_SECRET explicitly via conftest / env.
    """
    return os.environ.get("INTERNAL_JWT_SECRET", "")


ALGORITHM = "HS256"

# Must match aura/lib/auth/internal-jwt.ts — binds tokens to the Next→API hop
# so Google Calendar OAuth state JWTs (different aud) cannot be reused as Bearer.
INTERNAL_JWT_ISSUER = "aura-next"
INTERNAL_JWT_AUDIENCE = "aura-api"
GCAL_OAUTH_STATE_ISSUER = "aura-api"
GCAL_OAUTH_STATE_AUDIENCE = "aura-gcal-oauth"
GCAL_OAUTH_STATE_TYP = "gcal_oauth_state"

# Broad roles stored in user_identity_map.role — what the JWT carries.
# Fine-grained roles are in role_bindings and resolved by resolve_effective_role().
BROAD_ROLES = {"student", "faculty", "admin", "guest"}

# All possible effective roles (for DLS filter, Pinecone, admin panel)
ALL_ROLES = {
    "public",
    "student",
    # Batch-year student roles (derived from ERP ID prefix)
    "student_2026",
    "student_2025",
    "student_2024",
    "student_2023",
    "faculty_general",
    "faculty_coord",
    "faculty_convenor_ug",
    "faculty_convenor_pg",
    "dean_students",
    "dean_faculty",
    "dean_academic",
    "registrar",
    "admin_staff",
    "superadmin",
    "guest",
}

# ── Batch-year role resolution ─────────────────────────────────────────────
# CURRENT_BATCH_YEAR is the admission year of the current 1st-year batch.
# Update this env var each academic year; no code change required.
_CURRENT_BATCH_YEAR: int = int(os.environ.get("CURRENT_BATCH_YEAR", "2026"))

_YEAR_ROLE_MAP: dict[int, str] = {
    _CURRENT_BATCH_YEAR:     "student_2026",  # 1st year
    _CURRENT_BATCH_YEAR - 1: "student_2025",  # 2nd year
    _CURRENT_BATCH_YEAR - 2: "student_2024",  # 3rd year
    _CURRENT_BATCH_YEAR - 3: "student_2023",  # 4th year
}


def resolve_student_year_role(erp_id: str) -> str:
    """Derive the batch-year DLS role from a 9-digit student ERP ID.

    The first four characters of the ERP ID encode the admission year
    (e.g. '2026' in '202601001'). This is compared against
    CURRENT_BATCH_YEAR to produce a role such as 'student_2026'.

    Falls back to the generic 'student' role if the prefix is not a
    recognised batch year (e.g. PhD students or unrecognised IDs).
    """
    if erp_id and len(erp_id) >= 4 and erp_id[:4].isdigit():
        prefix = int(erp_id[:4])
        return _YEAR_ROLE_MAP.get(prefix, "student")
    return "student"


# auto_error=False so we can return 401 (not 403) for missing credentials.
security = HTTPBearer(auto_error=False)


@dataclass
class Identity:
    erp_id: str
    role:   str           # broad role from JWT: student | faculty | admin
    dept:   Optional[str] = None
    email:  Optional[str] = None
    # Timetable-cohort fields — display/lookup only, never used for authz.
    full_name:    Optional[str] = None
    current_year: Optional[int] = None
    current_sem:  Optional[int] = None
    current_sec:  Optional[str] = None

    @property
    def user_id(self) -> str:
        """Backward-compat alias."""
        return self.erp_id

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "erp_id": self.erp_id,
            "dept": self.dept,
            "email": self.email,
            "full_name": self.full_name,
            "current_year": self.current_year,
            "current_sem": self.current_sem,
            "current_sec": self.current_sec,
        }


def require_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Identity:
    """
    Verifies the HS256 internal JWT minted by Next.js.
    Raises 401 on missing/invalid/expired token, 403 on unrecognised role.
    Returns Identity with the BROAD role — callers that need the fine-grained
    role (coordinator, convenor, dean) call resolve_effective_role() from
    access_control.py, which queries role_bindings.
    """
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM],
            audience=INTERNAL_JWT_AUDIENCE,
            issuer=INTERNAL_JWT_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please refresh the page")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token")

    role   = claims.get("role", "")
    erp_id = claims.get("erpId", "")  # Next.js mints camelCase
    email  = claims.get("email") or None

    if not erp_id or not isinstance(erp_id, str):
        raise HTTPException(status_code=401, detail="Token missing erpId claim")
    # Bound claim sizes so a forged/minted JWT cannot inflate logs, Redis
    # quota keys, or DB params with megabyte-scale strings.
    if len(erp_id) > 64:
        raise HTTPException(status_code=401, detail="Invalid erpId claim")
    if role not in BROAD_ROLES:
        raise HTTPException(status_code=403, detail="Unrecognised role in token")
    if email is not None and (not isinstance(email, str) or len(email) > 320):
        raise HTTPException(status_code=401, detail="Invalid email claim")

    dept = claims.get("department")
    if dept is not None and (not isinstance(dept, str) or len(dept) > 128):
        raise HTTPException(status_code=401, detail="Invalid department claim")

    return Identity(
        erp_id=erp_id,
        role=role,
        dept=dept,
        email=email,
        full_name=claims.get("fullName") if isinstance(claims.get("fullName"), str) else None,
        current_year=claims.get("currentYear") if isinstance(claims.get("currentYear"), int) else None,
        current_sem=claims.get("currentSem") if isinstance(claims.get("currentSem"), int) else None,
        current_sec=claims.get("currentSec") if isinstance(claims.get("currentSec"), str) else None,
    )


get_current_identity = require_identity