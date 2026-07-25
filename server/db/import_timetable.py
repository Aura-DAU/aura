"""
import_timetable.py — load the master timetable (per year/sem/section) from
a CSV file into timetable_master. Run this once per semester when the
official timetable is published, and again whenever it changes.

Expected CSV columns (header row required, any order):
    year, sem, sec, day, start_time, end_time,
    course_code, course_name, session_type, room, faculty_name

  - year          : integer, e.g. 3
  - sem           : integer, e.g. 5
  - sec           : text, e.g. A
  - day           : weekday name, e.g. Monday (case-insensitive; Mon/Tue/... ok too)
  - start_time    : HH:MM 24-hour, e.g. 09:00
  - end_time      : HH:MM 24-hour, e.g. 10:30
  - course_code   : e.g. IT302
  - course_name   : e.g. Computer Networks
  - session_type  : lecture | lab | tutorial (defaults to "lecture" if blank)
  - room          : e.g. "Lab 3, Phase 1" (optional)
  - faculty_name  : e.g. "Dr. XYZ" (optional)

Usage:
    python server/db/import_timetable.py path/to/demo_timetable.csv
    python server/db/import_timetable.py path/to/demo_timetable.csv --replace-cohort
        (--replace-cohort deletes existing master rows for every
         (year, sem, sec) combination present in the file before inserting —
         use this when re-importing a corrected timetable, not when merging.)
"""

import csv
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import db.connection as db_conn  # noqa: E402
from rag.pipeline.timetable.service import parse_day, VALID_SESSION_TYPES  # noqa: E402


def _clean(row: dict) -> dict:
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}


def import_csv(path: str, replace_cohort: bool = False) -> int:
    cohorts_seen = set()
    inserted = 0

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [_clean(r) for r in reader]

    if replace_cohort:
        for row in rows:
            cohorts_seen.add((int(row["year"]), int(row["sem"]), row["sec"]))
        for year, sem, sec in cohorts_seen:
            db_conn.execute(
                "DELETE FROM timetable_master WHERE year = %s AND sem = %s AND sec = %s",
                (year, sem, sec),
            )
            print(f"Cleared existing master rows for year={year} sem={sem} sec={sec}")

    for i, row in enumerate(rows, start=2):  # start=2: header is line 1
        try:
            year = int(row["year"])
            sem = int(row["sem"])
            sec = row["sec"]
            day_of_week = parse_day(row["day"])
            session_type = (row.get("session_type") or "lecture").lower()
            if session_type not in VALID_SESSION_TYPES:
                raise ValueError(f"session_type must be one of {VALID_SESSION_TYPES}, got {session_type!r}")

            db_conn.execute(
                """INSERT INTO timetable_master
                     (year, sem, sec, day_of_week, start_time, end_time,
                      course_code, course_name, session_type, room, faculty_name)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    year, sem, sec, day_of_week, row["start_time"], row["end_time"],
                    row["course_code"], row["course_name"], session_type,
                    row.get("room") or None, row.get("faculty_name") or None,
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"Skipping row {i} ({row}): {e}", file=sys.stderr)

    return inserted


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("csv_path", help="Path to the demo/official timetable CSV file")
    parser.add_argument("--replace-cohort", action="store_true",
                         help="Delete existing rows for each (year, sem, sec) in the file before inserting")
    args = parser.parse_args()

    count = import_csv(args.csv_path, replace_cohort=args.replace_cohort)
    print(f"Imported {count} timetable_master rows from {args.csv_path}")
