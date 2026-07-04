"""
auth.py — FastAPI identity middleware (SSO architecture).

Authentication is owned entirely by NextAuth.js on the frontend.
FastAPI's only job here is to cryptographically verify the short-lived
internal JWT that Next.js mints (via jsonwebtoken) and attaches to every
request in the Authorization header.

Flow:
  1. User logs in via Google SSO → NextAuth.js handles everything.
  2. NextAuth jwt() callback calls GET /internal/resolve-identity?email=...
     to get the user's erp_id, role, and department from AURA's backend.
  3. Next.js mints a short-lived internal JWT:
       jwt.sign({ role, erpId, department }, INTERNAL_JWT_SECRET, { expiresIn: "60s" })
  4. Next.js attaches it as: Authorization: Bearer <token> on every request.
  5. require_identity() (this file) verifies the signature and extracts Identity.

FastAPI never issues tokens. FastAPI never stores passwords or sessions.
FastAPI never sets cookies.

Required env var:
  INTERNAL_JWT_SECRET — shared secret between Next.js and FastAPI.
  Must be ≥256 bits of random data, stored only in env/secrets-manager.
  Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
"""

import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

INTERNAL_JWT_SECRET = os.environ.get("INTERNAL_JWT_SECRET", "")
ALGORITHM           = "HS256"
VALID_ROLES         = {"student", "faculty", "admin"}

security = HTTPBearer()


@dataclass
class Identity:
    erp_id: str           # roll number (student) or employee ID (faculty)
    role:   str           # 'student' | 'faculty' | 'admin'
    dept:   str | None = None

    @property
    def user_id(self) -> str:
        """Backward-compat alias — erp_id is the stable identifier now."""
        return self.erp_id

    def as_dict(self) -> dict:
        return {"role": self.role, "erp_id": self.erp_id, "dept": self.dept}


def require_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Identity:
    """
    FastAPI dependency. Verifies the internal JWT minted by Next.js.
    Raises 401 on missing/invalid/expired token.
    Raises 403 on unrecognized role.
    On success, returns Identity — the single source of truth for
    who is making this request throughout the entire request lifecycle.
    """
    if not INTERNAL_JWT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="INTERNAL_JWT_SECRET is not configured on the server.",
        )

    token = credentials.credentials
    try:
        claims = jwt.decode(token, INTERNAL_JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Session expired — please refresh the page")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session token")

    role   = claims.get("role", "")
    erp_id = claims.get("erpId", "")   # Next.js mints camelCase "erpId"

    if not erp_id:
        raise HTTPException(status_code=401, detail="Token missing erpId claim")
    if role not in VALID_ROLES:
        raise HTTPException(status_code=403, detail=f"Unrecognized role: {role!r}")

    return Identity(
        erp_id=erp_id,
        role=role,
        dept=claims.get("department"),
    )


# Alias used in some route files
get_current_identity = require_identity
