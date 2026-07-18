# Database migration runner — lightweight alternative to Alembic for AURA's
# small Auth DB. Designed to run at server startup (or in a deployment script)
# AUTH_DB_URL: ${{ secrets.AUTH_DB_URL }}

import os
import sys
import argparse
import psycopg2
from psycopg2 import sql
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
TRACKING_TABLE = "_migrations"


def _conn(db_url: str):
    return psycopg2.connect(db_url)


def _ensure_tracking_table(cur) -> None:
    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} (
            filename    TEXT PRIMARY KEY,
            applied_at  TIMESTAMPTZ DEFAULT now()
        )
    """).format(sql.Identifier(TRACKING_TABLE)))


def _applied_migrations(cur) -> set[str]:
    cur.execute(sql.SQL("SELECT filename FROM {}").format(sql.Identifier(TRACKING_TABLE)))
    return {r[0] for r in cur.fetchall()}


def _migration_files() -> list[Path]:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print(f"[migrate] No .sql files found in {MIGRATIONS_DIR}")
    return files


def run(db_url: str, dry_run: bool = False) -> None:
    files = _migration_files()
    conn  = _conn(db_url)
    try:
        with conn.cursor() as cur:
            _ensure_tracking_table(cur)
            conn.commit()
            applied = _applied_migrations(cur)

        pending = [f for f in files if f.name not in applied]
        if not pending:
            print("[migrate] All migrations already applied — nothing to do.")
            return

        for migration_file in pending:
            migration_sql = migration_file.read_text(encoding="utf-8")
            print(f"[migrate] {'(dry-run) would apply' if dry_run else 'Applying'}: {migration_file.name}")
            if dry_run:
                continue
            try:
                with conn.cursor() as cur:
                    cur.execute(migration_sql)
                    cur.execute(
                        sql.SQL("INSERT INTO {} (filename) VALUES (%s)").format(
                            sql.Identifier(TRACKING_TABLE)
                        ),
                        (migration_file.name,),
                    )
                conn.commit()
                print(f"[migrate] [OK] Applied: {migration_file.name}")
            except Exception as e:
                conn.rollback()
                print(f"[migrate] [FAILED] {migration_file.name} - {e}")
                print("[migrate] Server startup aborted — fix the migration and redeploy.")
                sys.exit(1)

    finally:
        conn.close()


def status(db_url: str) -> None:
    files   = _migration_files()
    conn    = _conn(db_url)
    try:
        with conn.cursor() as cur:
            _ensure_tracking_table(cur)
            conn.commit()
            applied = _applied_migrations(cur)
    finally:
        conn.close()

    print(f"{'FILE':<45}  STATUS")
    print("-" * 60)
    for f in files:
        tag = "[OK] applied" if f.name in applied else "[PENDING]"
        print(f"{f.name:<45}  {tag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA DB migration runner")
    parser.add_argument("--db-url", default=os.environ.get("AUTH_DB_URL", ""),
                        help="PostgreSQL connection string (default: AUTH_DB_URL env var)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show which migrations would run without applying them")
    parser.add_argument("--status", action="store_true",
                        help="Show applied/pending status without running anything")
    args = parser.parse_args()

    if not args.db_url:
        print("ERROR: AUTH_DB_URL env var or --db-url argument is required.")
        sys.exit(1)

    if args.status:
        status(args.db_url)
    else:
        run(args.db_url, dry_run=args.dry_run)
