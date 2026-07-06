"""
Timetable parsing — deliberately kept separate from parsers.py because this
is the one piece of data that does double duty: it answers "what are my
classes" for a student AND is the sole input for deriving a faculty
member's teaching schedule (see faculty_schedule.py). Per your instruction,
AURA does not scrape eCampus *as* faculty to get this — it only needs to
get *better at deriving* it from whatever timetable data is already being
pulled on the student side, since every timetable entry carries an
instructor name.

TODO: confirm exactly which page renders this (see pages.py — Pages.TIMETABLE
is a best guess) and the real column layout, the same way as parsers.py.
"""

from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class TimetableEntry:
    course_code: str
    course_name: str
    instructor: str
    day: str            # e.g. "Monday"
    start_time: str      # e.g. "09:00"
    end_time: str        # e.g. "09:50"
    room: str
    section: str | None = None  # batch/section, if the page distinguishes them


def parse_timetable(html: str) -> list[TimetableEntry]:
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []
    table = max(tables, key=lambda t: len(t.find_all("tr")))

    # TODO confirm real column order — this is a reasonable guess for a
    # weekly-grid-style timetable export rendered as a flat table.
    headers = ["course_code", "course_name", "instructor", "day", "start_time", "end_time", "room"]

    entries = []
    for tr in table.find_all("tr")[1:]:
        cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
        if len(cells) < len(headers):
            continue
        row = dict(zip(headers, cells))
        entries.append(TimetableEntry(
            course_code=row["course_code"],
            course_name=row["course_name"],
            instructor=row["instructor"],
            day=row["day"],
            start_time=row["start_time"],
            end_time=row["end_time"],
            room=row["room"],
        ))
    return entries
