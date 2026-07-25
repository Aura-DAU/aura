"""
import_timetable_xlsx.py — CLI tool to parse a DAU timetable XLSX file
and import the structured records into the timetable_master PostgreSQL table.

Replaces the CSV-based import_timetable.py with a robust XLSX parser that
handles merged cells, multi-section courses, and the DAU-specific layout.

Usage
=====
    # Dry run (parse and show summary, no DB write)
    python import_timetable_xlsx.py path/to/timetable.xlsx --dry-run

    # Import into the database
    python import_timetable_xlsx.py path/to/timetable.xlsx --semester "Winter 2026"

    # Export to JSON/CSV for inspection
    python import_timetable_xlsx.py path/to/timetable.xlsx --json output.json
    python import_timetable_xlsx.py path/to/timetable.xlsx --csv output.csv

    # Query student/faculty view without DB
    python import_timetable_xlsx.py path/to/timetable.xlsx --student BTech 2 ICT A
    python import_timetable_xlsx.py path/to/timetable.xlsx --faculty PD
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to path for imports
_script_dir = Path(__file__).resolve().parent
_server_dir = _script_dir.parent  # server/
_rag_dir = _server_dir / "rag"
sys.path.insert(0, str(_rag_dir))

from pipeline.timetable.xlsx_parser import (
    TimetableRecord,
    faculty_view,
    parse_timetable,
    student_view,
    summary,
    to_dicts,
)

logger = logging.getLogger("aura.import_timetable")


def _import_to_db(records: list[TimetableRecord], semester_label: str, db_url: str) -> int:
    """
    Insert parsed timetable records into the timetable_master table.

    Workflow:
    1. Delete all existing rows for the given semester_label (idempotent re-import).
    2. Batch-insert the new records.
    3. Return the count of inserted rows.
    """
    try:
        import psycopg2
    except ImportError:
        logger.error("psycopg2 not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    try:
        # Clear existing data for this semester (idempotent)
        cur.execute(
            "DELETE FROM timetable_master WHERE semester_label = %s",
            (semester_label,),
        )
        deleted = cur.rowcount
        if deleted > 0:
            logger.info("Cleared %d existing rows for semester '%s'.", deleted, semester_label)

        # Batch insert
        insert_sql = """
            INSERT INTO timetable_master (
                year, sem, sec, day_of_week, start_time, end_time,
                course_code, course_name, session_type, room, faculty_name,
                credits, course_type, batch_raw, branch, program, semester_label
            ) VALUES (
                %(year)s, %(semester)s, %(section)s, %(day_of_week)s,
                %(start_time)s, %(end_time)s,
                %(course_code)s, %(course_name)s, %(session_type)s,
                %(room)s, %(faculty_initials)s,
                %(credits)s, %(course_type)s, %(batch_raw)s,
                %(branch)s, %(program)s, %(semester_label)s
            )
        """
        count = 0
        for r in records:
            params = {
                "year": r.year,
                "semester": r.semester,
                "section": r.section or "",
                "day_of_week": r.day_of_week,
                "start_time": r.start_time,
                "end_time": r.end_time,
                "course_code": r.course_code,
                "course_name": r.course_name,
                "session_type": r.session_type,
                "room": r.room,
                "faculty_initials": r.faculty_initials,
                "credits": r.credits,
                "course_type": r.course_type,
                "batch_raw": r.batch_raw,
                "branch": r.branch,
                "program": r.program,
                "semester_label": semester_label,
            }
            cur.execute(insert_sql, params)
            count += 1

        conn.commit()
        logger.info("Inserted %d records for semester '%s'.", count, semester_label)
        return count

    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Parse a DAU timetable XLSX file and optionally import to PostgreSQL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("xlsx_path", help="Path to the XLSX timetable file.")
    parser.add_argument("--sheet", default="Time-Table", help="Sheet name (default: Time-Table).")

    # Output options
    output_group = parser.add_argument_group("Output options")
    output_group.add_argument("--json", dest="json_out", metavar="PATH", help="Export as JSON.")
    output_group.add_argument("--csv", dest="csv_out", metavar="PATH", help="Export as CSV.")
    output_group.add_argument("--summary", action="store_true", help="Print summary statistics.")
    output_group.add_argument("--dry-run", action="store_true", help="Parse and show summary without DB import.")

    # DB import options
    db_group = parser.add_argument_group("Database import")
    db_group.add_argument("--semester", metavar="LABEL", help="Semester label (e.g. 'Winter 2026'). Required for DB import.")
    db_group.add_argument("--db-url", default=os.environ.get("AUTH_DB_URL", ""), help="PostgreSQL connection URL. Defaults to AUTH_DB_URL env var.")

    # Filter options
    filter_group = parser.add_argument_group("Filter (view without DB)")
    filter_group.add_argument(
        "--student", nargs="+", metavar=("PROGRAM", "SEM"),
        help="Student view: --student BTech 2 ICT A"
    )
    filter_group.add_argument("--faculty", metavar="INITIALS", help="Faculty view: --faculty PD")

    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Parse the XLSX
    logger.info("Parsing: %s", args.xlsx_path)
    records = parse_timetable(args.xlsx_path, sheet_name=args.sheet)
    logger.info("Parsed %d records.", len(records))

    # Apply filters
    if args.student:
        program = args.student[0]
        sem = int(args.student[1])
        branch = args.student[2] if len(args.student) > 2 else ""
        section = args.student[3] if len(args.student) > 3 else None
        records = student_view(records, program, sem, branch, section)
        label = f"{program} Sem-{sem} {branch} {f'Section {section}' if section else ''}"
        print(f"\n[Student Timetable] {label.strip()} ({len(records)} classes/week)\n")
        _print_table(records, mode="student")

    if args.faculty:
        records = faculty_view(records, args.faculty)
        print(f"\n[Faculty Timetable] {args.faculty} ({len(records)} classes/week)\n")
        _print_table(records, mode="faculty")

    # Summary
    if args.summary or args.dry_run:
        stats = summary(records)
        print("\n[Summary]")
        print("-" * 40)
        for k, v in stats.items():
            if isinstance(v, list) and len(v) > 15:
                print(f"  {k}: {len(v)} items")
            else:
                print(f"  {k}: {v}")

    # JSON export
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(to_dicts(records), f, indent=2, ensure_ascii=False)
        logger.info("JSON written to %s (%d records)", args.json_out, len(records))

    # CSV export
    if args.csv_out:
        dicts = to_dicts(records)
        if dicts:
            fieldnames = list(dicts[0].keys())
            with open(args.csv_out, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dicts)
            logger.info("CSV written to %s (%d records)", args.csv_out, len(records))

    # DB import
    if args.semester and not args.dry_run:
        if not args.db_url:
            logger.error("No database URL. Set AUTH_DB_URL env var or use --db-url.")
            sys.exit(1)
        count = _import_to_db(records, args.semester, args.db_url)
        logger.info("Database import complete: %d rows.", count)
    elif not (args.json_out or args.csv_out or args.summary or args.dry_run or args.student or args.faculty):
        # Default: dry run with summary
        stats = summary(records)
        print(f"\nParsed {len(records)} class records from {args.xlsx_path}")
        print(f"  Batches:  {stats['unique_batches']}")
        print(f"  Courses:  {stats['unique_courses']}")
        print(f"  Faculty:  {stats['unique_faculty']}")
        print(f"  Sessions: {stats['session_types']}")
        print(f"\nUse --dry-run for full summary, --json/--csv to export,")
        print(f"or --semester 'Winter 2026' to import into the database.")


def _print_table(records: list[TimetableRecord], mode: str = "student"):
    """Print records as a formatted console table."""
    if mode == "student":
        header = f"{'Day':<10} {'Time':<14} {'Code':<10} {'Course':<42} {'Sec':<5} {'Type':<8} {'Faculty':<8} {'Room'}"
        print(header)
        print("-" * len(header))
        for r in records:
            sec = r.section or "-"
            name = r.course_name[:40]
            print(f"  {r.day:<10} {r.start_time}-{r.end_time}  {r.course_code:<10} {name:<42} {sec:<5} {r.session_type:<8} {r.faculty_initials:<8} {r.room}")
    elif mode == "faculty":
        header = f"{'Day':<10} {'Time':<14} {'Batch':<35} {'Code':<10} {'Course':<32} {'Sec':<5} {'Room'}"
        print(header)
        print("-" * len(header))
        for r in records:
            sec = r.section or "-"
            name = r.course_name[:30]
            print(f"  {r.day:<10} {r.start_time}-{r.end_time}  {r.batch_raw:<35} {r.course_code:<10} {name:<32} {sec:<5} {r.room}")


if __name__ == "__main__":
    main()
