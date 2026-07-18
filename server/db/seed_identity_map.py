# seed_identity_map.py — Populate user_identity_map from an ERP CSV export.
# Replaces the old seed_users.py. Key differences:
# python seed_identity_map.py users.csv --deactivate-missing

import csv
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import db.connection as db_conn

VALID_ROLES    = {"student", "faculty", "admin"}
ALLOWED_DOMAINS = {"dau.ac.in", "daiict.ac.in"}

from typing import Optional


def _validate_row(row: dict, line: int) -> Optional[dict]:
    erp_id = row.get("erp_id", "").strip()
    email  = row.get("email",  "").strip().lower()
    role   = row.get("role",   "").strip().lower()
    dept   = row.get("dept",   "").strip() or None

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
    return {"erp_id": erp_id, "email": email, "role": role, "dept": dept}


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
        "SELECT erp_id, email, role, dept, is_active FROM user_identity_map WHERE erp_id = %s",
        (user["erp_id"],),
    )
    if not existing:
        if not dry_run:
            db_conn.execute(
                "INSERT INTO user_identity_map (erp_id, email, role, dept) VALUES (%s,%s,%s,%s)",
                (user["erp_id"], user["email"], user["role"], user["dept"]),
            )
        return "INSERT"
    ex = existing[0]
    changed = (
        ex["email"] != user["email"] or ex["role"] != user["role"] or
        ex["dept"] != user["dept"] or not ex["is_active"]
    )
    if changed:
        if not dry_run:
            db_conn.execute(
                "UPDATE user_identity_map SET email=%s, role=%s, dept=%s, is_active=TRUE WHERE erp_id=%s",
                (user["email"], user["role"], user["dept"], user["erp_id"]),
            )
        return "UPDATE"
    return "NOOP"


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
    for user in rows:
        action = upsert(user, dry_run=args.dry_run)
        counts[action] += 1
        if action != "NOOP":
            tag = "[DRY]" if args.dry_run else "     "
            print(f"  {tag} [{action}] {user['erp_id']} / {user['email']} ({user['role']})")

    print(f"\nSummary: {counts['INSERT']} inserted, {counts['UPDATE']} updated, {counts['NOOP']} unchanged.")

    if args.deactivate_missing:
        n = deactivate_missing({r["erp_id"] for r in rows}, dry_run=args.dry_run)
        print(f"Deactivated: {n} users not in CSV.")


if __name__ == "__main__":
    main()
