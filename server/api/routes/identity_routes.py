# GET /internal/resolve-identity — Next.js-only email → ERP identity lookup.
# Requires X-Internal-Secret; validates @dau.ac.in / @daiict.ac.in before DB hit.
# Optionally restrict by source IP via INTERNAL_RESOLVE_ALLOWLIST (comma-separated).
import ipaddress
import os
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}


def _allowlist() -> list[str]:
    raw = os.environ.get("INTERNAL_RESOLVE_ALLOWLIST", "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return ""


def _ip_allowed(client_ip: str, entries: list[str]) -> bool:
    if not client_ip:
        return False
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for entry in entries:
        try:
            if "/" in entry:
                if addr in ipaddress.ip_network(entry, strict=False):
                    return True
            elif addr == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


def _validate_secret(
    request: Request,
    x_internal_secret: str = Header(..., alias="X-Internal-Secret"),
) -> None:
    # Depends()-wired secret check (compare_digest) + optional IP allowlist.
    if not INTERNAL_RESOLVE_SECRET:
        raise HTTPException(
            status_code=500,
            detail="INTERNAL_RESOLVE_SECRET is not configured on the server.",
        )
    if not secrets.compare_digest(x_internal_secret, INTERNAL_RESOLVE_SECRET):
        raise HTTPException(status_code=403, detail="Forbidden")

    allowed = _allowlist()
    if allowed and not _ip_allowed(_client_ip(request), allowed):
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
        # Valid domain but no identity map row yet — do not echo the email.
        raise HTTPException(
            status_code=404,
            detail=(
                "No active AURA account found for this email. "
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
