"""Persist corpus-aligned AcademicScope rows from login identity.

Maps dept codes written into ``user_identity_map`` (e.g. ICT, ICTCS) onto the
``programme_id`` / ``degree_level`` vocabulary used by the academic corpus
(e.g. ``btech-ict``), then upserts ``student_identity`` +
``student_academic_profile`` so ``AcademicScopeResolver`` can resolve scope.

Gaps / best-effort limits (documented intentionally):
- ICTCS → ``btech-ict`` (no separate ``btech-ict-cs`` corpus taxonomy yet).
- MTech → ``mtech-ict`` (email/dept alone cannot distinguish EC vs ICT).
- ``admission_year`` from the first four digits of a 9-digit ERP id when present.
- ``curriculum_version`` / ``regulation_version`` are not available from identity.
- Course enrolment snapshot is not populated here (LEFT JOIN stays empty).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from api.auth import Identity

logger = logging.getLogger(__name__)

DERIVATION_RULE_VERSION = "v1"
SOURCE_SYSTEM = "aura_identity_resolve"

# Dept codes from identity_routes / user_identity_map → corpus programme ids.
# Aligned with ingestion/chunking/metadata_extractors.py programme_patterns.
_DEPT_TO_PROGRAMME: dict[str, tuple[str, str]] = {
    "ICT": ("btech-ict", "undergraduate"),
    "ICTCS": ("btech-ict", "undergraduate"),  # prefer btech-ict until CS corpus exists
    "MnC": ("btech-mnc", "undergraduate"),
    "EVD": ("btech-evd", "undergraduate"),
    "MTech": ("mtech-ict", "postgraduate"),
    "MScIT": ("msc-it", "postgraduate"),
    "MScDS": ("msc-ds", "postgraduate"),
    "PhD": ("phd", "doctoral"),
}

_DEGREE_DURATION_YEARS = {
    "undergraduate": 4,
    "postgraduate": 2,
    "doctoral": 5,
}


@dataclass(frozen=True)
class DerivedAcademicIdentity:
    erp_id: str
    admission_year: int
    programme_id: str
    degree_level: str
    department_id: Optional[str]
    branch_id: Optional[str]
    expected_graduation_year: Optional[int]


def map_dept_to_programme(dept: Optional[str]) -> Optional[tuple[str, str]]:
    """Return ``(programme_id, degree_level)`` for a dept code, or None."""
    if not dept:
        return None
    return _DEPT_TO_PROGRAMME.get(dept.strip())


def infer_admission_year(erp_id: str) -> Optional[int]:
    """Best-effort admission year from a 9-digit student ERP id (YYYY…)."""
    if not erp_id or not re.match(r"^\d{9}$", erp_id):
        return None
    year = int(erp_id[:4])
    if 2000 <= year <= 2100:
        return year
    return None


def infer_dept_from_erp_id(erp_id: str) -> Optional[str]:
    """Best-effort dept code from a 9-digit student ERP id (same rules as identity resolve)."""
    if not erp_id or not re.match(r"^\d{9}$", erp_id):
        return None
    prog3 = erp_id[4:7]
    prog2 = erp_id[4:6]
    if prog3 == "014":
        return "ICTCS"
    if prog2 == "01":
        return "ICT"
    if prog2 == "03":
        return "MnC"
    if prog2 == "04":
        return "EVD"
    if prog2 == "11":
        return "MTech"
    if prog2 == "12":
        return "MScIT"
    if prog2 == "18":
        return "MScDS"
    if prog2 == "21":
        return "PhD"
    return None


def _lookup_dept_from_identity_map(erp_id: str) -> Optional[str]:
    """Read dept from user_identity_map when JWT/identity omitted it."""
    try:
        import db.connection as db_conn

        rows = db_conn.query(
            "SELECT dept FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE LIMIT 1",
            (erp_id,),
        )
        if rows and rows[0].get("dept"):
            return str(rows[0]["dept"]).strip() or None
    except Exception as exc:
        logger.warning("dept lookup failed for %s: %s", erp_id, exc)
    return None


def derive_academic_identity(
    *,
    erp_id: str,
    dept: Optional[str],
    admission_year: Optional[int] = None,
) -> Optional[DerivedAcademicIdentity]:
    """Build corpus-aligned identity fields from ERP id + dept code."""
    mapped = map_dept_to_programme(dept)
    if not mapped:
        return None
    programme_id, degree_level = mapped
    year = admission_year if admission_year is not None else infer_admission_year(erp_id)
    if year is None:
        return None
    duration = _DEGREE_DURATION_YEARS.get(degree_level)
    expected = (year + duration) if duration else None
    # ICTCS keeps a distinct department label; programme stays btech-ict.
    branch_id = "ict-cs" if (dept or "").strip() == "ICTCS" else None
    return DerivedAcademicIdentity(
        erp_id=erp_id,
        admission_year=year,
        programme_id=programme_id,
        degree_level=degree_level,
        department_id=(dept.strip() if dept else None),
        branch_id=branch_id,
        expected_graduation_year=expected,
    )


def upsert_student_academic_scope(
    *,
    erp_id: str,
    dept: Optional[str],
    admission_year: Optional[int] = None,
) -> bool:
    """Upsert ``student_identity`` + ``student_academic_profile``.

    Returns True when a row was written (or already consistent after upsert).
    Returns False when fields cannot be derived or the write fails.
    Requires a pre-existing ``user_identity_map`` row (FK).
    """
    derived = derive_academic_identity(
        erp_id=erp_id,
        dept=dept,
        admission_year=admission_year,
    )
    if derived is None:
        logger.warning(
            "Cannot derive academic scope for erp_id=%s dept=%s",
            erp_id,
            dept,
        )
        return False

    try:
        import db.connection as db_conn

        db_conn.execute(
            """
            INSERT INTO student_identity (
                erp_id, admission_year, programme_id, branch_id, department_id,
                degree_level, derivation_rule_version, identity_version, resolved_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, NOW())
            ON CONFLICT (erp_id) DO UPDATE SET
                admission_year = EXCLUDED.admission_year,
                programme_id = EXCLUDED.programme_id,
                branch_id = EXCLUDED.branch_id,
                department_id = EXCLUDED.department_id,
                degree_level = EXCLUDED.degree_level,
                derivation_rule_version = EXCLUDED.derivation_rule_version,
                identity_version = student_identity.identity_version + 1,
                resolved_at = NOW()
            """,
            (
                derived.erp_id,
                derived.admission_year,
                derived.programme_id,
                derived.branch_id,
                derived.department_id,
                derived.degree_level,
                DERIVATION_RULE_VERSION,
            ),
        )
        db_conn.execute(
            """
            INSERT INTO student_academic_profile (
                erp_id, academic_status, expected_graduation_year,
                curriculum_version, regulation_version, source_system,
                source_record_version, profile_version, synced_at, updated_at
            ) VALUES (%s, 'active', %s, NULL, NULL, %s, %s, 1, NOW(), NOW())
            ON CONFLICT (erp_id) DO UPDATE SET
                academic_status = 'active',
                expected_graduation_year = COALESCE(
                    EXCLUDED.expected_graduation_year,
                    student_academic_profile.expected_graduation_year
                ),
                source_system = EXCLUDED.source_system,
                source_record_version = EXCLUDED.source_record_version,
                profile_version = student_academic_profile.profile_version + 1,
                synced_at = NOW(),
                updated_at = NOW()
            """,
            (
                derived.erp_id,
                derived.expected_graduation_year,
                SOURCE_SYSTEM,
                DERIVATION_RULE_VERSION,
            ),
        )
        return True
    except Exception as exc:
        logger.warning(
            "Failed to upsert academic scope for %s: %s",
            erp_id,
            exc,
        )
        return False


def ensure_student_academic_scope(identity: Identity) -> bool:
    """Derive and persist academic scope from a request Identity (chat backfill)."""
    if getattr(identity, "role", None) != "student":
        return False
    erp_id = getattr(identity, "erp_id", None)
    if not erp_id:
        return False
    dept = getattr(identity, "dept", None)
    if not dept:
        dept = _lookup_dept_from_identity_map(erp_id) or infer_dept_from_erp_id(erp_id)
    return upsert_student_academic_scope(
        erp_id=erp_id,
        dept=dept,
        admission_year=infer_admission_year(erp_id),
    )
