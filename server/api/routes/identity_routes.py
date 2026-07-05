"""
identity_routes.py — Internal identity resolution endpoint.

Exposes exactly one endpoint:
  GET /internal/resolve-identity?email=<institutional_email>

Called exclusively by Next.js (inside the NextAuth jwt() callback) once
per user login to resolve a Google email into the ERP identity AURA needs.
Never called by a browser directly.

Security:
  - Requires X-Internal-Secret header matching INTERNAL_RESOLVE_SECRET env var.
  - Should be network-restricted to the Next.js server IP in production
    (nginx/firewall rule), but the secret header is a defense-in-depth layer.
  - Validates that the email domain is @dau.ac.in or @daiict.ac.in before
    doing any DB lookup.

Returns:
  { "erp_id": "202301234", "role": "student", "department": "ICT" }

Next.js uses this to populate the jwt() callback, then mints the internal
JWT that FastAPI's require_identity() verifies on every chat request.
"""

import os
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header, Query
import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}


def _validate_secret(x_internal_secret: str = Header(..., alias="X-Internal-Secret")) -> None:
    """FastAPI dependency — validates the X-Internal-Secret header.
    Wired via Depends() so secret checking is not duplicated inline."""
    if not INTERNAL_RESOLVE_SECRET:
        raise HTTPException(
            status_code=500,
            detail="INTERNAL_RESOLVE_SECRET is not configured on the server.",
        )
    if not secrets.compare_digest(x_internal_secret, INTERNAL_RESOLVE_SECRET):
        raise HTTPException(status_code=403, detail="Forbidden")


def _validate_email_domain(email: str) -> None:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    if domain not in ALLOWED_DOMAINS:
        raise HTTPException(
            status_code=400,
            detail=f"Email domain '{domain}' is not an authorised DAU domain.",
        )


@router.get("/resolve-identity")
def resolve_identity(
    email: str = Query(..., description="Institutional Google email to resolve"),
    _: None = Depends(_validate_secret),   # Fix #9: auth enforced via Depends
):
    """
    Resolve a Google institutional email to an ERP identity.
    Called by Next.js inside the NextAuth jwt() callback — not by browsers.
    """
    # 1. Domain validation (secret already verified by Depends(_validate_secret))
    _validate_email_domain(email)

    # 3. Look up in user_identity_map
    rows = db_conn.query(
        """SELECT erp_id, role, dept
           FROM user_identity_map
           WHERE email = %s AND is_active = TRUE""",
        (email.lower().strip(),),
    )

    if not rows:
        # Email is from a valid domain but has no identity mapping yet.
        # This happens for new staff/students not yet in the identity map.
        # Return 404 so Next.js can show a clear "Account not set up" message
        # rather than a generic auth error.
        raise HTTPException(
            status_code=404,
            detail=(
                f"No active AURA account found for {email}. "
                "If you are a DAU student or faculty member, please contact "
                "the AURA administrator to have your account activated."
            ),
        )

    row = rows[0]
    return {
        "erp_id":     row["erp_id"],
        "role":       row["role"],
        "department": row["dept"],
    }
