# Derives a faculty member's weekly teaching schedule from timetable data that
# was already scraped — never logs into eCampus as faculty, never needs a
# many (more complete).

from collections import defaultdict
from .timetable import TimetableEntry

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _entry_key(e: TimetableEntry) -> tuple:
    # Dedup key — the same class slot may appear in many different
    # students' timetables (everyone in the section sees the same row).
    return (e.course_code, e.day, e.start_time, e.end_time, e.instructor)


def build_faculty_schedule(timetable_entries: list[TimetableEntry], faculty_name: str) -> dict:
    # timetable_entries: pooled TimetableEntry objects from however many
    # student timetables have been scraped/cached so far (see cache.py — a
    # room, section}, ... ], ... } sorted by day-of-week then start time.
    needle = faculty_name.strip().lower()
    seen = set()
    matched = []

    for e in timetable_entries:
        if needle not in e.instructor.strip().lower():
            continue
        key = _entry_key(e)
        if key in seen:
            continue
        seen.add(key)
        matched.append(e)

    schedule: dict[str, list[dict]] = defaultdict(list)
    for e in matched:
        schedule[e.day].append({
            "course_code": e.course_code,
            "course_name": e.course_name,
            "start_time": e.start_time,
            "end_time": e.end_time,
            "room": e.room,
            "section": e.section,
        })

    for day in schedule:
        schedule[day].sort(key=lambda c: c["start_time"])

    ordered = {day: schedule[day] for day in DAY_ORDER if day in schedule}

    return {
        "faculty_name": faculty_name,
        "schedule": ordered,
        "course_count": len({c["course_code"] for day in ordered.values() for c in day}),
        "coverage_note": (
            "Derived from pooled student timetable data — may be incomplete "
            "if not every section taught by this faculty member has been "
            "seen yet in scraped timetables."
        ),
    }
