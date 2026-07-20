"""
identity_routes.py — Internal identity resolution endpoint.

Exposes exactly one endpoint:
  GET /internal/resolve-identity?email=<institutional_email>

Called exclusively by Next.js (inside the NextAuth jwt() callback) once
per user login to resolve a Google email into the ERP identity AURA needs.
Never called by a browser directly.

Security:
  - Requires X-Internal-Secret header matching INTERNAL_RESOLVE_SECRET env var.
  - Optional INTERNAL_RESOLVE_ALLOWLIST (comma-separated IPs/CIDRs).
  - Should be network-restricted to the Next.js server IP in production
    (nginx/firewall rule); the secret header is defense-in-depth.
  - Validates that the email domain is @dau.ac.in or @daiict.ac.in before
    doing any DB lookup.

Returns:
  { "erp_id": "202301234", "role": "student", "department": "ICT",
    "full_name": "Parth Agrawal", "current_year": 3, "current_sem": 5,
    "current_sec": "A" }

  full_name/current_year/current_sem/current_sec are only populated for
  students and are used purely to render the correct timetable cohort —
  they are never used for authorization decisions (the ERP DB remains
  the source of truth for anything academic).

Next.js uses this to populate the jwt() callback, then mints the internal
JWT that FastAPI's require_identity() verifies on every chat request.
"""

import ipaddress
import json
import os
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}

# Load pre-compiled faculty email prefixes on startup
FACULTY_EMAILS_PATH = Path(__file__).resolve().parent.parent / "faculty_emails.json"
FACULTY_EMAILS: set[str] = set()
if FACULTY_EMAILS_PATH.exists():
    try:
        with open(FACULTY_EMAILS_PATH, "r", encoding="utf-8") as f:
            FACULTY_EMAILS = set(json.load(f))
    except Exception as e:
        print(f"Warning: Failed to load faculty_emails.json: {e}")


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
    """Validates X-Internal-Secret and optional IP allowlist."""
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
    """
    Resolve a Google institutional email to an ERP identity.
    Called by Next.js inside the NextAuth jwt() callback — not by browsers.
    """
    _validate_email_domain(email)

    rows = db_conn.query(
        """SELECT erp_id, role, dept, full_name, current_year, current_sem, current_sec
           FROM user_identity_map
           WHERE email = %s AND is_active = TRUE""",
        (email.lower().strip(),),
    )

    if rows:
        row = rows[0]
        return {
            "erp_id": row["erp_id"],
            "role": row["role"],
            "department": row["dept"],
            "full_name": row.get("full_name"),
            "current_year": row.get("current_year"),
            "current_sem": row.get("current_sem"),
            "current_sec": row.get("current_sec"),
        }

    # Fallback to dynamic classification (no email echoed in error paths).
    prefix = email.split("@")[0].lower().strip()
    role = "guest"
    erp_id = f"GUEST_{prefix.upper()}"
    dept = None

    # Check Student: 9-digit roll number
    if re.match(r"^\d{9}$", prefix):
        year = int(prefix[:4])
        if 2023 <= year <= 2026:
            role = "student"
            erp_id = prefix
            dept = "ICT"
    # Check Faculty: matched prefix from pre-compiled list
    elif prefix in FACULTY_EMAILS:
        role = "faculty"
        erp_id = f"FAC_{prefix.upper()}"
        dept = "ICT"

    # Insert valid student/faculty into user_identity_map as write-through cache
    if role in ("student", "faculty"):
        try:
            db_conn.execute(
                """INSERT INTO user_identity_map (email, erp_id, role, dept, is_active)
                   VALUES (%s, %s, %s, %s, TRUE)
                   ON CONFLICT (email) DO UPDATE
                   SET erp_id = EXCLUDED.erp_id, role = EXCLUDED.role,
                       dept = EXCLUDED.dept, is_active = TRUE""",
                (email.lower().strip(), erp_id, role, dept),
            )
        except Exception as db_err:
            print(f"Warning: Failed to cache dynamic user in DB: {db_err}")

    return {
        "erp_id": erp_id,
        "role": role,
        "department": dept,
        "full_name": None,
        "current_year": None,
        "current_sem": None,
        "current_sec": None,
    }
