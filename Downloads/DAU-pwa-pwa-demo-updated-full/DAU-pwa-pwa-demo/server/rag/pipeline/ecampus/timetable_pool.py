"""
Accumulates TimetableEntry rows seen across every student's get_timetable()
call, so build_faculty_schedule() has more than just one student's partial
view to work with over time. Non-sensitive data (class slot/room/instructor,
not tied to who's asking), so this can live in a plain sqlite file rather
than the encrypted vault.
"""

import os
import sqlite3
from pathlib import Path
from .timetable import TimetableEntry

DB_PATH = Path(os.environ.get("ECAMPUS_TIMETABLE_POOL_DB", "/var/lib/aura/timetable_pool.db"))


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS timetable_entries (
            course_code TEXT, course_name TEXT, instructor TEXT,
            day TEXT, start_time TEXT, end_time TEXT, room TEXT, section TEXT,
            PRIMARY KEY (course_code, day, start_time, end_time, instructor)
        )
    """)
    return conn


def append_entries(entries: list[TimetableEntry]) -> None:
    if not entries:
        return
    with _connect() as conn:
        conn.executemany(
            """INSERT OR REPLACE INTO timetable_entries
               (course_code, course_name, instructor, day, start_time, end_time, room, section)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [(e.course_code, e.course_name, e.instructor, e.day, e.start_time, e.end_time, e.room, e.section)
             for e in entries],
        )


def load_all_entries() -> list[TimetableEntry]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT course_code, course_name, instructor, day, start_time, end_time, room, section "
            "FROM timetable_entries"
        ).fetchall()
    return [TimetableEntry(*row) for row in rows]
