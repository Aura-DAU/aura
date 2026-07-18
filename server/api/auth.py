# FastAPI identity middleware — verifies Next.js-minted HS256 JWT (never issues tokens).
# JWT claims: { erpId, role, department, email?, exp }; role is broad (student|faculty|admin|guest).
# Fine-grained roles resolved via role_bindings / access_control.resolve_effective_role().
import os
from dataclasses import dataclass
from typing import Optional

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


def get_internal_jwt_secret() -> str:
    # Empty means misconfigured — callers should return HTTP 500.
    return os.environ.get("INTERNAL_JWT_SECRET", "")


HASHING_ALGORITHM = "HS256"

# Broad roles in user_identity_map / JWT; fine-grained roles live in role_bindings.
BROAD_ROLES = {"student", "faculty", "admin", "guest"}

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

# auto_error=False → missing credentials become 401, not 403.
security = HTTPBearer(auto_error=False)


@dataclass
class Identity:
    erp_id: str
    role: str  # broad: student | faculty | admin
    dept: Optional[str] = None
    email: Optional[str] = None

    @property
    def user_id(self) -> str:
        # Backward-compat alias for erp_id.
        return self.erp_id

    def as_dict(self) -> dict:
        return {
            "role": self.role,
            "erp_id": self.erp_id,
            "dept": self.dept,
            "email": self.email,
        }


def require_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Identity:
    # Verify HS256 JWT; 401 missing/invalid/expired, 403 unknown role.
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = credentials.credentials
    try:
        claims = jwt.decode(token, secret, algorithms=[HASHING_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please refresh the page")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token")

    role = claims.get("role", "")
    erp_id = claims.get("erpId", "")  # Next.js mints camelCase
    email = claims.get("email") or None

    if not erp_id:
        raise HTTPException(status_code=401, detail="Token missing erpId claim")
    if role not in BROAD_ROLES:
        raise HTTPException(status_code=403, detail=f"Unrecognised role in token: {role!r}")

    return Identity(erp_id=erp_id, role=role, dept=claims.get("department"), email=email)


get_current_identity = require_identity
