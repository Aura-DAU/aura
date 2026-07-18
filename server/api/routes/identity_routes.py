# GET /internal/resolve-identity — Next.js-only email → ERP identity lookup.
# Requires X-Internal-Secret; validates @dau.ac.in / @daiict.ac.in before DB hit.
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query

import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}


def _validate_secret(x_internal_secret: str = Header(..., alias="X-Internal-Secret")) -> None:
    # Depends()-wired secret check (compare_digest).
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
    _: None = Depends(_validate_secret),
):
    # Called from NextAuth jwt() callback — not from browsers.
    _validate_email_domain(email)

    rows = db_conn.query(
        """SELECT erp_id, role, dept
           FROM user_identity_map
           WHERE email = %s AND is_active = TRUE""",
        (email.lower().strip(),),
    )

    if not rows:
        # Valid domain but no identity map row yet.
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
        "erp_id": row["erp_id"],
        "role": row["role"],
        "department": row["dept"],
    }
