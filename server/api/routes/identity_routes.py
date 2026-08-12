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
import logging
import os
import re
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request

import db.connection as db_conn
from api.academic_scope_persist import upsert_student_academic_scope

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["internal"])


def _persist_student_scope(erp_id: str, role: str, dept) -> None:
    """Best-effort write of AcademicScope tables after identity resolve."""
    if role != "student" or not erp_id:
        return
    try:
        upsert_student_academic_scope(erp_id=erp_id, dept=dept)
    except Exception as exc:
        logger.warning("Failed to persist academic scope for %s: %s", erp_id, exc)

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
        logger.warning("Failed to load faculty_emails.json: %s", e)


def _allowlist() -> list[str]:
    raw = os.environ.get("INTERNAL_RESOLVE_ALLOWLIST", "").strip()
    if not raw:
        return []
    return [part.strip() for part in raw.split(",") if part.strip()]


def _client_ip(request: Request) -> str:
    # Prefer the direct peer (request.client.host). Do NOT trust X-Forwarded-For
    # here — when the backend is reached without a trusted reverse-proxy hop
    # (or if host port 8000 were ever published), forged XFF would bypass the
    # allowlist. Nginx still sets XFF for logging; allowlist uses the TCP peer.
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


def _infer_role_and_cohort(email: str) -> dict:
    """Infer student/faculty/guest role, branch (dept), and default cohort from email.

    Branch is read off digits 5-6 (0-indexed [4:6]) of the 9-digit student id,
    e.g. 202601010 -> "01". Current (2026 batch) mapping:
        01 ICT/CS   03 MnC   04 EVD   05 CS-AI   06 ECE-AI
        31 BS-MS DS 32 BS-MS IT
    (11/12/18/21 are existing PG/PhD codes, unrelated to this table.)
    Digits 5-7 == "014" is the pre-existing ICT-CS specialization override
    within the 01 (ICT) branch and takes precedence over the 2-digit table.
    """
    prefix = email.split("@")[0].lower().strip()
    role = "guest"
    erp_id = f"GUEST_{prefix.upper()}"
    dept = None
    year = None
    sem = None
    sec = None

    if re.match(r"^\d{9}$", prefix):
        entry_year = int(prefix[:4])
        if 2023 <= entry_year <= 2026:
            import datetime
            now_year = datetime.datetime.now().year
            year = max(1, min(4, (now_year - entry_year) + 1))
            sem = year * 2 - 1
            sec = "A"
            role = "student"
            erp_id = prefix

        prog3 = prefix[4:7]
        prog2 = prefix[4:6]
        if prog3 == "014":
            dept = "ICTCS"
        elif prog2 == "01":
            dept = "ICT"
        elif prog2 == "03":
            dept = "MnC"
        elif prog2 == "04":
            dept = "EVD"
        elif prog2 == "05":
            dept = "CSAI"
        elif prog2 == "06":
            dept = "ECEAI"
        elif prog2 == "11":
            dept = "MTech"
        elif prog2 == "12":
            dept = "MScIT"
        elif prog2 == "18":
            dept = "MScDS"
        elif prog2 == "21":
            dept = "PhD"
        elif prog2 == "31":
            dept = "BSMSDS"
        elif prog2 == "32":
            dept = "BSMSIT"
        else:
            dept = "ICT"

    elif prefix in FACULTY_EMAILS:
        role = "faculty"
        erp_id = f"FAC_{prefix.upper()}"
        dept = "ICT"

    return {
        "role": role,
        "erp_id": erp_id,
        "dept": dept,
        "current_year": year,
        "current_sem": sem,
        "current_sec": sec,
    }


@router.get("/resolve-identity")
def resolve_identity(
    email: str = Query(..., min_length=3, max_length=320, description="Institutional Google email to resolve"),
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
        yr = row.get("current_year")
        sem = row.get("current_sem")
        sec = row.get("current_sec")
        dept = row.get("dept")
        if (yr is None or sem is None or not sec or not dept) and row.get("erp_id") and re.match(r"^\d{9}$", row["erp_id"]):
            inferred = _infer_role_and_cohort(email)
            yr = yr if yr is not None else inferred["current_year"]
            sem = sem if sem is not None else inferred["current_sem"]
            sec = sec if sec else inferred["current_sec"]
            dept = dept if dept else inferred["dept"]

        _persist_student_scope(row["erp_id"], row["role"], dept)

        return {
            "erp_id": row["erp_id"],
            "role": row["role"],
            "department": dept,
            "full_name": row.get("full_name"),
            "current_year": yr,
            "current_sem": sem,
            "current_sec": sec,
        }

    # Fallback to dynamic classification
    inferred = _infer_role_and_cohort(email)
    role = inferred["role"]
    erp_id = inferred["erp_id"]
    dept = inferred["dept"]
    current_year = inferred["current_year"]
    current_sem = inferred["current_sem"]
    current_sec = inferred["current_sec"]

    if role in ("student", "faculty"):
        try:
            db_conn.execute(
                """INSERT INTO user_identity_map (email, erp_id, role, dept, current_year, current_sem, current_sec, is_active)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                   ON CONFLICT (email) DO UPDATE
                   SET erp_id = EXCLUDED.erp_id, role = EXCLUDED.role,
                       dept = EXCLUDED.dept,
                       current_year = COALESCE(user_identity_map.current_year, EXCLUDED.current_year),
                       current_sem = COALESCE(user_identity_map.current_sem, EXCLUDED.current_sem),
                       current_sec = COALESCE(user_identity_map.current_sec, EXCLUDED.current_sec),
                       is_active = TRUE""",
                (email.lower().strip(), erp_id, role, dept, current_year, current_sem, current_sec),
            )
        except Exception as db_err:
            logger.warning("Failed to cache dynamic user in DB: %s", db_err)

        # Scope tables FK user_identity_map — only after the map row exists.
        _persist_student_scope(erp_id, role, dept)

    return {
        "erp_id": erp_id,
        "role": role,
        "department": dept,
        "full_name": None,
        "current_year": current_year,
        "current_sem": current_sem,
        "current_sec": current_sec,
    }
