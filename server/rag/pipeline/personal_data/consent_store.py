"""
consent_store.py — AURA's internal advisor-consent store.

Replaces the old credentials_vault.py consent functions.
Reads from AURA's own consent_grants table (NOT the ERP DB).
No write operations in the ERP — AURA is read-only externally.

Table schema (AURA's internal DB):
  consent_grants (
    student_erp_id  TEXT NOT NULL,
    faculty_erp_id  TEXT NOT NULL,
    granted_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    revoked_at      TIMESTAMPTZ,
    PRIMARY KEY (student_erp_id, faculty_erp_id)
  )
"""

import os
import psycopg2
import psycopg2.extras

def _conn():
    return psycopg2.connect(os.environ["AUTH_DB_URL"])


def has_advisor_consent(student_erp_id: str, faculty_erp_id: str) -> bool:
    """Return True if the student has granted this faculty member access."""
    with _conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT 1 FROM consent_grants
                   WHERE student_erp_id = %s AND faculty_erp_id = %s
                     AND revoked_at IS NULL
                   LIMIT 1""",
                (student_erp_id, faculty_erp_id),
            )
            return cur.fetchone() is not None


def list_consented_faculty(student_erp_id: str) -> list[dict]:
    """Return all faculty members the student has granted access to."""
    with _conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """SELECT faculty_erp_id, granted_at
                   FROM consent_grants
                   WHERE student_erp_id = %s AND revoked_at IS NULL
                   ORDER BY granted_at DESC""",
                (student_erp_id,),
            )
            return [dict(r) for r in cur.fetchall()]
