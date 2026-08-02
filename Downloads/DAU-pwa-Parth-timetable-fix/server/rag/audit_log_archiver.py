# Audit log archiver — run as a cron job (e.g. weekly via crontab or a
# systemd timer) to prevent unbounded audit_log table growth.
# Set AURA_ADMIN_DB_URL accordingly.

import os
import sys
import json
import gzip
import argparse
import datetime
from pathlib import Path

# Allow running standalone
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import psycopg2
import psycopg2.extras

ARCHIVE_AGE_DAYS = int(os.environ.get("AUDIT_ARCHIVE_AGE_DAYS", "90"))
ARCHIVE_DIR      = Path(os.environ.get("AUDIT_ARCHIVE_DIR", "/var/lib/aura/audit_archive"))
# Needs DELETE grant — use a separate admin connection string, not aura_app
ADMIN_DB_URL     = os.environ.get("AURA_ADMIN_DB_URL") or os.environ.get("AUTH_DB_URL", "")


def _admin_conn():
    if not ADMIN_DB_URL:
        raise RuntimeError("AURA_ADMIN_DB_URL (or AUTH_DB_URL) not set")
    return psycopg2.connect(ADMIN_DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _fetch_old_rows(conn, cutoff: datetime.datetime) -> list[dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM audit_log WHERE ts < %s ORDER BY ts ASC",
            (cutoff,),
        )
        return [dict(r) for r in cur.fetchall()]


def _write_archive_file(rows: list[dict], cutoff: datetime.datetime) -> Path:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    fname = ARCHIVE_DIR / f"audit_log_{cutoff.strftime('%Y%m%d')}.jsonl.gz"
    with gzip.open(fname, "wt", encoding="utf-8") as f:
        for row in rows:
            # Make all values JSON-serialisable
            serializable = {
                k: (v.isoformat() if isinstance(v, datetime.datetime) else v)
                for k, v in row.items()
            }
            f.write(json.dumps(serializable) + "\n")
    return fname


def _delete_old_rows(conn, cutoff: datetime.datetime) -> int:
    with conn.cursor() as cur:
        cur.execute("DELETE FROM audit_log WHERE ts < %s", (cutoff,))
        return cur.rowcount


def run(dry_run: bool = False, age_days: int = ARCHIVE_AGE_DAYS) -> None:
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=age_days)
    print(f"[archiver] Archiving audit_log rows older than {cutoff.date()} (>{age_days} days)")

    conn = _admin_conn()
    try:
        rows = _fetch_old_rows(conn, cutoff)
        if not rows:
            print("[archiver] Nothing to archive.")
            return

        print(f"[archiver] Found {len(rows)} rows to archive.")

        if dry_run:
            print("[archiver] DRY RUN — no files written, no rows deleted.")
            return

        archive_path = _write_archive_file(rows, cutoff)
        print(f"[archiver] Written: {archive_path}  ({archive_path.stat().st_size:,} bytes compressed)")

        deleted = _delete_old_rows(conn, cutoff)
        conn.commit()
        print(f"[archiver] Deleted {deleted} rows from audit_log.")

    except Exception as e:
        conn.rollback()
        print(f"[archiver] ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive and prune old audit_log rows")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--days", type=int, default=ARCHIVE_AGE_DAYS,
                        help="Archive rows older than this many days (default: 90)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, age_days=args.days)
