"""
seed_identity_map.py — Populate user_identity_map from an ERP CSV export.

Replaces the old seed_users.py. Key differences:
  - No password columns (auth is handled by Google SSO via NextAuth.js)
  - No sessions table or hashing
  - Idempotent: re-running updates changed rows, never duplicates

CSV format (header row required):
  erp_id, email, role, dept, full_name, current_year, current_sem, current_sec

  full_name/current_year/current_sem/current_sec are optional and only
  meaningful for role=student — they're what lets AURA show the right
  timetable cohort. Leave them blank for faculty/admin rows.

Example:
  202301234, parth.a@daiict.ac.in, student, ICT, Parth Agrawal, 3, 5, A
  FAC001, prof.sharma@daiict.ac.in, faculty, ICT, Dr. Sharma, , ,

Run at the start of each semester to pick up new students/faculty and
deactivate departed ones. The --deactivate-missing flag marks users
absent from the CSV as is_active=FALSE, which blocks /internal/resolve-identity
for them immediately.

Usage:
  python seed_identity_map.py users.csv
  python seed_identity_map.py users.csv --dry-run
  python seed_identity_map.py users.csv --deactivate-missing
"""

import csv
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db.connection as db_conn
from api.academic_scope_persist import (
    DERIVATION_RULE_VERSION,
    upsert_student_academic_scope,
)

VALID_ROLES    = {"student", "faculty", "admin"}
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}

from typing import Optional


def _validate_row(row: dict, line: int) -> Optional[dict]:
    erp_id = row.get("erp_id", "").strip()
    email  = row.get("email",  "").strip().lower()
    role   = row.get("role",   "").strip().lower()
    dept   = row.get("dept",   "").strip() or None
    full_name = (row.get("full_name") or "").strip() or None

    def _int_or_none(key: str) -> Optional[int]:
        val = (row.get(key) or "").strip()
        if not val:
            return None
        try:
            return int(val)
        except ValueError:
            print(f"  [SKIP] line {line}: {key} must be an integer, got {val!r}")
            return None

    current_year = _int_or_none("current_year")
    current_sem = _int_or_none("current_sem")
    current_sec = (row.get("current_sec") or "").strip() or None

    if not erp_id or not email:
        print(f"  [SKIP] line {line}: missing erp_id or email")
        return None
    domain = email.split("@")[-1] if "@" in email else ""
    if domain not in ALLOWED_DOMAINS:
        print(f"  [SKIP] line {line}: email domain '{domain}' not in allowed list")
        return None
    if role not in VALID_ROLES:
        print(f"  [SKIP] line {line}: invalid role '{role}' for {erp_id}")
        return None
    return {
        "erp_id": erp_id, "email": email, "role": role, "dept": dept,
        "full_name": full_name, "current_year": current_year,
        "current_sem": current_sem, "current_sec": current_sec,
    }


def load_csv(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            validated = _validate_row({k.strip(): v for k, v in row.items()}, i)
            if validated:
                rows.append(validated)
    return rows


def upsert(user: dict, dry_run: bool) -> str:
    existing = db_conn.query(
        """SELECT erp_id, email, role, dept, is_active,
                  full_name, current_year, current_sem, current_sec
           FROM user_identity_map WHERE erp_id = %s""",
        (user["erp_id"],),
    )
    if not existing:
        if not dry_run:
            db_conn.execute(
                """INSERT INTO user_identity_map
                     (erp_id, email, role, dept, full_name, current_year, current_sem, current_sec)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
                (user["erp_id"], user["email"], user["role"], user["dept"],
                 user["full_name"], user["current_year"], user["current_sem"], user["current_sec"]),
            )
        return "INSERT"
    ex = existing[0]
    changed = (
        ex["email"] != user["email"] or ex["role"] != user["role"] or
        ex["dept"] != user["dept"] or not ex["is_active"] or
        ex["full_name"] != user["full_name"] or ex["current_year"] != user["current_year"] or
        ex["current_sem"] != user["current_sem"] or ex["current_sec"] != user["current_sec"]
    )
    if changed:
        if not dry_run:
            db_conn.execute(
                """UPDATE user_identity_map
                   SET email=%s, role=%s, dept=%s, is_active=TRUE,
                       full_name=%s, current_year=%s, current_sem=%s, current_sec=%s
                   WHERE erp_id=%s""",
                (user["email"], user["role"], user["dept"],
                 user["full_name"], user["current_year"], user["current_sem"], user["current_sec"],
                 user["erp_id"]),
            )
        return "UPDATE"
    return "NOOP"


def sync_academic_scope(user: dict, dry_run: bool) -> str:
    """Ensure seeded students have the derived rows required by retrieval."""
    if user["role"] != "student":
        return "SKIP"

    rows = db_conn.query(
        """SELECT si.department_id, si.derivation_rule_version,
                  sap.erp_id AS profile_erp_id
           FROM student_identity si
           LEFT JOIN student_academic_profile sap ON sap.erp_id = si.erp_id
           WHERE si.erp_id = %s""",
        (user["erp_id"],),
    )
    if (
        rows
        and rows[0]["department_id"] == user["dept"]
        and rows[0]["derivation_rule_version"] == DERIVATION_RULE_VERSION
        and rows[0]["profile_erp_id"] is not None
    ):
        return "NOOP"
    if dry_run:
        return "SYNC"

    synced = upsert_student_academic_scope(
        erp_id=user["erp_id"],
        dept=user["dept"],
    )
    return "SYNC" if synced else "ERROR"


def deactivate_missing(csv_ids: set[str], dry_run: bool) -> int:
    active = db_conn.query("SELECT erp_id FROM user_identity_map WHERE is_active=TRUE")
    missing = {r["erp_id"] for r in active} - csv_ids
    for erp_id in missing:
        print(f"  [DEACTIVATE] {erp_id}")
        if not dry_run:
            db_conn.execute(
                "UPDATE user_identity_map SET is_active=FALSE WHERE erp_id=%s", (erp_id,)
            )
    return len(missing)


def main():
    parser = argparse.ArgumentParser(description="Seed AURA user_identity_map from ERP CSV")
    parser.add_argument("csv_path")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--deactivate-missing", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN — no changes will be written.\n")

    rows = load_csv(args.csv_path)
    print(f"Loaded {len(rows)} valid rows.\n")

    counts = {"INSERT": 0, "UPDATE": 0, "NOOP": 0}
    scope_counts = {"SYNC": 0, "NOOP": 0, "SKIP": 0, "ERROR": 0}
    for user in rows:
        action = upsert(user, dry_run=args.dry_run)
        counts[action] += 1
        if action != "NOOP":
            tag = "[DRY]" if args.dry_run else "     "
            print(f"  {tag} [{action}] {user['erp_id']} / {user['email']} ({user['role']})")

        scope_action = sync_academic_scope(user, dry_run=args.dry_run)
        scope_counts[scope_action] += 1
        if scope_action in {"SYNC", "ERROR"}:
            tag = "[DRY]" if args.dry_run else "     "
            print(f"  {tag} [SCOPE {scope_action}] {user['erp_id']}")

    print(f"\nSummary: {counts['INSERT']} inserted, {counts['UPDATE']} updated, {counts['NOOP']} unchanged.")
    print(
        "Academic scope: "
        f"{scope_counts['SYNC']} synced, {scope_counts['NOOP']} unchanged, "
        f"{scope_counts['SKIP']} not applicable, {scope_counts['ERROR']} failed."
    )

    if args.deactivate_missing:
        n = deactivate_missing({r["erp_id"] for r in rows}, dry_run=args.dry_run)
        print(f"Deactivated: {n} users not in CSV.")

    if scope_counts["ERROR"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
