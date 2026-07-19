# GET /internal/resolve-identity — Next.js-only email → ERP identity lookup.
# Requires X-Internal-Secret; validates @dau.ac.in / @daiict.ac.in before DB hit.
import os
import secrets
import re
import json
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query
import db.connection as db_conn

router = APIRouter(prefix="/internal", tags=["internal"])

INTERNAL_RESOLVE_SECRET = os.environ.get("INTERNAL_RESOLVE_SECRET", "")
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}

# Load pre-compiled faculty email prefixes on startup
FACULTY_EMAILS_PATH = Path(__file__).resolve().parent.parent / "faculty_emails.json"
FACULTY_EMAILS = set()
if FACULTY_EMAILS_PATH.exists():
    try:
        with open(FACULTY_EMAILS_PATH, "r", encoding="utf-8") as f:
            FACULTY_EMAILS = set(json.load(f))
    except Exception as e:
        print(f"Warning: Failed to load faculty_emails.json: {e}")


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

    if rows:
        row = rows[0]
        return {
            "erp_id":     row["erp_id"],
            "role":       row["role"],
            "department": row["dept"],
        }

    # Fallback to dynamic classification
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
            dept = "ICT"  # Default student department
    # Check Faculty: matched prefix from pre-compiled list
    elif prefix in FACULTY_EMAILS:
        role = "faculty"
        erp_id = f"FAC_{prefix.upper()}"
        dept = "ICT"  # Default faculty department

    # Insert valid student/faculty into user_identity_map as write-through cache
    if role in ("student", "faculty"):
        try:
            db_conn.execute(
                """INSERT INTO user_identity_map (email, erp_id, role, dept, is_active)
                   VALUES (%s, %s, %s, %s, TRUE)
                   ON CONFLICT (email) DO UPDATE 
                   SET erp_id = EXCLUDED.erp_id, role = EXCLUDED.role, dept = EXCLUDED.dept, is_active = TRUE""",
                (email.lower().strip(), erp_id, role, dept),
            )
        except Exception as db_err:
            print(f"Warning: Failed to cache dynamic user {email} in DB: {db_err}")

    return {
        "erp_id":     erp_id,
        "role":       role,
        "department": dept,
    }


