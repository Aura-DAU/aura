"""
Encrypted storage for per-user eCampus credentials (Option A from the guide).

This is the single most security-sensitive file in the whole integration —
it is the only place a student's eCampus password touches AURA's
infrastructure. Treat changes to this file with the same rigor as anything
touching auth.

Design choices and why:
  - Fernet (symmetric AES) encryption at rest, keyed by a secret that lives
    ONLY in environment/secrets-manager config, never in source control.
  - Credentials are looked up by the student's AURA-verified erp_id (from
    the signed internal JWT — see the RBAC guide), never by anything
    client-supplied.
  - No plaintext password is ever logged. If you add logging here later,
    audit it specifically for this.
  - This module deliberately does NOT cache decrypted passwords in memory
    beyond the single login() call that needs them.

Before going to production, get sign-off (from whoever owns DAU's data
protection policy) on storing student portal passwords at all — pushing for
Option B (proper backend access, no stored passwords) remains the better
long-term answer; this module exists to unblock a working prototype now.
"""

import os
import json
import sqlite3
from pathlib import Path
from cryptography.fernet import Fernet

# Fix #2: VAULT_KEY was read at module level, so a missing env var crashed the
# entire server at startup even when the scrape path was never exercised.
# Replaced with a lazy getter so the error surfaces only when credentials
# are actually needed.
_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        key = os.environ.get("ECAMPUS_VAULT_KEY")
        if not key:
            raise RuntimeError(
                "ECAMPUS_VAULT_KEY is not set. Generate one with "
                "Fernet.generate_key() and add it to your .env / secrets manager."
            )
        from cryptography.fernet import Fernet as _Fernet
        _fernet = _Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet

DB_PATH = Path(os.environ.get("ECAMPUS_VAULT_DB", "/var/lib/aura/ecampus_credentials.db"))


class CredentialsNotLinked(Exception):
    """Raised when a student hasn't completed the 'Connect your eCampus
    account' step yet. The caller should prompt them to link it, not fail
    silently."""
    pass


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ecampus_credentials (
            erp_id TEXT PRIMARY KEY,
            encrypted_blob BLOB NOT NULL,
            linked_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS advisor_consent (
            student_erp_id TEXT NOT NULL,
            faculty_erp_id TEXT NOT NULL,
            granted_at TEXT NOT NULL,
            PRIMARY KEY (student_erp_id, faculty_erp_id)
        )
    """)
    # Restrict vault DB permissions when possible (Unix).
    try:
        os.chmod(DB_PATH, 0o600)
    except OSError:
        pass
    return conn


def store_credentials(erp_id: str, ecampus_username: str, ecampus_password: str) -> None:
    """Called once, during the explicit 'Connect your eCampus account' flow —
    never inferred or auto-populated from any other source."""
    blob = json.dumps({"username": ecampus_username, "password": ecampus_password}).encode()
    encrypted = _get_fernet().encrypt(blob)
    with _connect() as conn:
        conn.execute(
            """INSERT INTO ecampus_credentials (erp_id, encrypted_blob, linked_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(erp_id) DO UPDATE SET
                 encrypted_blob = excluded.encrypted_blob,
                 linked_at = excluded.linked_at""",
            (erp_id, encrypted),
        )


def get_credentials(erp_id: str) -> tuple[str, str]:
    """Returns (username, password). Raises CredentialsNotLinked if the
    student hasn't connected their eCampus account yet."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT encrypted_blob FROM ecampus_credentials WHERE erp_id = ?",
            (erp_id,),
        ).fetchone()
    if not row:
        raise CredentialsNotLinked(
            f"No eCampus credentials linked for {erp_id}. "
            "Prompt the user to connect their eCampus account first."
        )
    decrypted = _get_fernet().decrypt(row[0])
    data = json.loads(decrypted)
    return data["username"], data["password"]


def unlink_credentials(erp_id: str) -> None:
    """Lets a student revoke AURA's access to their eCampus account at any
    time — surface this clearly in the UI, not just as a buried API call."""
    with _connect() as conn:
        conn.execute("DELETE FROM ecampus_credentials WHERE erp_id = ?", (erp_id,))


def is_linked(erp_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM ecampus_credentials WHERE erp_id = ?", (erp_id,)
        ).fetchone()
    return row is not None


# ── Advisor consent ──────────────────────────────────────────────────────
# Under the per-student credential model, AURA never holds a faculty
# member's ability to read a student's data "because they're advising
# them" — it only ever has whatever the STUDENT explicitly authorized.
# These functions are the only source of truth for that authorization, and
# ecampus/composite_tools.py:get_advisee_snapshot checks has_advisor_consent()
# before access_control.authorize_personal_query() ever runs.

def grant_advisor_consent(student_erp_id: str, faculty_erp_id: str) -> None:
    """Student-initiated only — never call this from a faculty-facing code
    path. The UI for this should show the faculty member's name clearly
    before the student confirms."""
    with _connect() as conn:
        conn.execute(
            """INSERT INTO advisor_consent (student_erp_id, faculty_erp_id, granted_at)
               VALUES (?, ?, datetime('now'))
               ON CONFLICT(student_erp_id, faculty_erp_id) DO UPDATE SET
                 granted_at = excluded.granted_at""",
            (student_erp_id, faculty_erp_id),
        )


def revoke_advisor_consent(student_erp_id: str, faculty_erp_id: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM advisor_consent WHERE student_erp_id = ? AND faculty_erp_id = ?",
            (student_erp_id, faculty_erp_id),
        )


def has_advisor_consent(student_erp_id: str, faculty_erp_id: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM advisor_consent WHERE student_erp_id = ? AND faculty_erp_id = ?",
            (student_erp_id, faculty_erp_id),
        ).fetchone()
    return row is not None


def list_consented_faculty(student_erp_id: str) -> list[str]:
    """For the student-facing 'who currently has access to my data' UI."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT faculty_erp_id FROM advisor_consent WHERE student_erp_id = ?",
            (student_erp_id,),
        ).fetchall()
    return [r[0] for r in rows]


def list_consenting_students(faculty_erp_id: str) -> list[str]:
    """For a faculty member's view: which students have shared data with them."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT student_erp_id FROM advisor_consent WHERE faculty_erp_id = ?",
            (faculty_erp_id,),
        ).fetchall()
    return [r[0] for r in rows]
