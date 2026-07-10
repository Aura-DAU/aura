"""
auth.py — FastAPI identity middleware (SSO / Next.js JWT architecture).

FastAPI never issues tokens. It only verifies the short-lived internal JWT
that Next.js mints after Google SSO, then attaches to every request.

JWT claim shape (minted by Next.js):
  { erpId, role, department, exp }
  role is the BROAD role from user_identity_map: student | faculty | admin
  Fine-grained roles (faculty_coord, dean_students, etc.) are resolved
  server-side via role_bindings — see access_control.resolve_effective_role()
"""

import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

def get_internal_jwt_secret() -> str:
    return os.environ.get("INTERNAL_JWT_SECRET", "test-internal-secret-for-auth-middleware")
ALGORITHM           = "HS256"

# Broad roles stored in user_identity_map.role — what the JWT carries.
# Fine-grained roles are in role_bindings and resolved by resolve_effective_role().
BROAD_ROLES = {"student", "faculty", "admin", "guest"}

# All possible effective roles (for DLS filter, Pinecone, admin panel)
ALL_ROLES = {
    "public",
    "student",
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

# auto_error=False so we can return 401 (not 403) for missing credentials.
security = HTTPBearer(auto_error=False)


@dataclass
class Identity:
    erp_id: str
    role:   str           # broad role from JWT: student | faculty | admin
    dept:   Optional[str] = None

    @property
    def user_id(self) -> str:
        """Backward-compat alias."""
        return self.erp_id

    def as_dict(self) -> dict:
        return {"role": self.role, "erp_id": self.erp_id, "dept": self.dept}


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
        claims = jwt.decode(token, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please refresh the page")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token")

    role   = claims.get("role", "")
    erp_id = claims.get("erpId", "")  # Next.js mints camelCase

    if not erp_id:
        raise HTTPException(status_code=401, detail="Token missing erpId claim")
    if role not in BROAD_ROLES:
        raise HTTPException(status_code=403, detail=f"Unrecognised role in token: {role!r}")

    return Identity(erp_id=erp_id, role=role, dept=claims.get("department"))


get_current_identity = require_identity