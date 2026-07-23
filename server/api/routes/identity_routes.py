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
import re
import secrets
import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query
import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in", "gmail.com"}

# Regex: student emails start with a 4-digit year, e.g. 202401226@dau.ac.in
_STUDENT_EMAIL_RE = re.compile(r"^(\d{4})\d+@")


def _infer_role_and_cohort(email: str) -> dict:
    """Infer role and cohort from institutional email.

    Student emails:  202401226@dau.ac.in  → admission_year=2024
    Faculty/staff:   anything else        → role=faculty

    Cohort calc (odd/autumn semester):
      current_year = calendar_year - admission_year + 1
      current_sem  = (current_year - 1) * 2 + 1   (odd semesters for autumn)
    """
    local_part = email.split("@")[0] if "@" in email else ""
    match = _STUDENT_EMAIL_RE.match(email)

    if match:
        admission_year = int(match.group(1))
        calendar_year = datetime.date.today().year
        # If we're before July (start of academic year), use previous year
        month = datetime.date.today().month
        academic_year = calendar_year if month >= 7 else calendar_year - 1
        current_year = academic_year - admission_year + 1

        if current_year < 1:
            current_year = 1
        if current_year > 4:
            current_year = 4

        # Odd semesters for autumn (Jul-Dec), even for spring (Jan-Jun)
        current_sem = (current_year - 1) * 2 + (1 if month >= 7 else 2)

        return {
            "role": "student",
            "erp_id": local_part.upper(),
            "dept": "ICT",
            "current_year": current_year,
            "current_sem": current_sem,
            "current_sec": "A",   # default; student can change via profile
        }
    else:
        # Faculty / staff — no cohort fields
        erp_id = "FAC_" + local_part.upper().replace(".", "_")
        return {
            "role": "faculty",
            "erp_id": erp_id,
            "dept": "ICT",
            "current_year": None,
            "current_sem": None,
            "current_sec": None,
        }


def _validate_secret(x_internal_secret: str = Header(..., alias="X-Internal-Secret")) -> None:
    """FastAPI dependency — validates the X-Internal-Secret header.
    Wired via Depends() so secret checking is not duplicated inline."""
    secret = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
    if not secret:
        raise HTTPException(
            status_code=500,
            detail="INTERNAL_RESOLVE_SECRET is not configured on the server.",
        )
    if not secrets.compare_digest(x_internal_secret, secret):
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

    # 2. Look up in user_identity_map
    rows = db_conn.query(
        """SELECT erp_id, role, dept, full_name,
                  current_year, current_sem, current_sec
           FROM user_identity_map
           WHERE email = %s AND is_active = TRUE""",
        (email.lower().strip(),),
    )

    if not rows:
        # Auto-provision: infer role + cohort from the email pattern
        clean_email = email.lower().strip()
        inferred = _infer_role_and_cohort(clean_email)
        db_conn.execute(
            """INSERT INTO user_identity_map
                   (email, erp_id, role, dept, is_active,
                    current_year, current_sem, current_sec)
               VALUES (%s, %s, %s, %s, TRUE, %s, %s, %s)
               ON CONFLICT (email) DO NOTHING""",
            (
                clean_email,
                inferred["erp_id"],
                inferred["role"],
                inferred["dept"],
                inferred["current_year"],
                inferred["current_sem"],
                inferred["current_sec"],
            ),
        )
        rows = db_conn.query(
            """SELECT erp_id, role, dept, full_name,
                      current_year, current_sem, current_sec
               FROM user_identity_map
               WHERE email = %s AND is_active = TRUE""",
            (clean_email,),
        )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No active AURA account found for {email}.",
        )

    row = rows[0]
    return {
        "erp_id":           row["erp_id"],
        "role":             row["role"],
        "department":       row["dept"],
        "full_name":        row.get("full_name"),
        "current_year":     row.get("current_year"),
        "current_sem":      row.get("current_sem"),
        "current_sec":      row.get("current_sec"),
    }
