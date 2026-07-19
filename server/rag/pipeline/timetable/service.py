"""
service.py — resolves a student's *effective* timetable (cohort master
merged with that student's own overrides) and applies new overrides.

Security invariant, enforced everywhere in this file: every write is scoped
to `identity.erp_id` taken from the verified internal JWT. There is no code
path here that accepts a student_id/erp_id argument from tool call
arguments — a student can only ever change their own timetable.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Optional

import db.connection as db_conn

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VALID_SESSION_TYPES = {"lecture", "lab", "tutorial"}


@dataclass
class _CohortLookup:
    """Minimal identity-shaped object for scheduler-side lookups, which run
    outside a request context and therefore have no verified JWT/Identity —
    only the erp_id + cohort fields already read from the DB."""
    role: str
    erp_id: str
    current_year: int
    current_sem: int
    current_sec: str


class TimetableError(Exception):
    """Raised for user-facing validation problems (bad day name, missing cohort, etc.)."""


def _field(identity, name: str):
    """Reads a field off `identity` whether it's the api.auth.Identity
    dataclass (attribute access, used by FastAPI routes) or a plain dict
    (used by the ecampus-style agent orchestrator tool-calling convention)."""
    if isinstance(identity, dict):
        return identity.get(name)
    return getattr(identity, name, None)


# Public alias — tool_registry.py and other callers outside this module use
# this name instead of reaching for the "_"-prefixed one.
field = _field


def day_name(day_of_week: int) -> str:
    return DAY_NAMES[day_of_week] if 0 <= day_of_week <= 6 else "Unknown"


def parse_day(value) -> int:
    """Accepts an int 0-6, or a day name/abbreviation (case-insensitive)."""
    if isinstance(value, int):
        if 0 <= value <= 6:
            return value
        raise TimetableError("day_of_week must be between 0 (Monday) and 6 (Sunday).")
    text = str(value).strip().lower()
    for idx, name in enumerate(DAY_NAMES):
        if text == name.lower() or text == name[:3].lower():
            return idx
    raise TimetableError(f"Could not understand the day '{value}'. Use a weekday name like 'Tuesday'.")


def _fmt_time(t) -> str:
    if t is None:
        return ""
    if isinstance(t, str):
        return t[:5]
    return t.strftime("%H:%M")


def _require_cohort(identity) -> tuple[int, int, str]:
    role = _field(identity, "role")
    if role != "student":
        raise TimetableError("Only students have a personal timetable in AURA.")
    year, sem, sec = _field(identity, "current_year"), _field(identity, "current_sem"), _field(identity, "current_sec")
    if year is None or sem is None or not sec:
        raise TimetableError(
            "Your year/semester/section isn't set up yet in AURA — please contact the AURA "
            "administrator so your profile can be linked to a timetable cohort."
        )
    return year, sem, sec


def get_master_rows(year: int, sem: int, sec: str) -> list[dict]:
    return db_conn.query(
        """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name
           FROM timetable_master
           WHERE year = %s AND sem = %s AND sec = %s
           ORDER BY day_of_week, start_time""",
        (year, sem, sec),
    )


def get_overrides(erp_id: str) -> list[dict]:
    return db_conn.query(
        """SELECT id, erp_id, kind, master_id, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name, note
           FROM timetable_overrides
           WHERE erp_id = %s AND is_active = TRUE
           ORDER BY day_of_week, start_time""",
        (erp_id,),
    )


def _row_to_slot(row: dict, is_custom: bool = False, override_id=None) -> dict:
    return {
        "id": str(override_id or row["id"]),
        "day_of_week": row["day_of_week"],
        "day": day_name(row["day_of_week"]),
        "start_time": _fmt_time(row["start_time"]),
        "end_time": _fmt_time(row["end_time"]),
        "course_code": row["course_code"],
        "course_name": row["course_name"],
        "session_type": row["session_type"],
        "room": row.get("room"),
        "faculty_name": row.get("faculty_name"),
        "is_custom": is_custom,
    }


def get_effective_timetable(identity) -> dict:
    """Returns {"cohort": {...}, "timetable": [slot, ...]} sorted by day/time,
    for the identity's own (year, sem, sec), merged with their overrides."""
    year, sem, sec = _require_cohort(identity)
    master_rows = {row["id"]: row for row in get_master_rows(year, sem, sec)}
    overrides = get_overrides(_field(identity, "erp_id"))

    removed_master_ids = {o["master_id"] for o in overrides if o["kind"] == "remove" and o["master_id"]}
    replace_by_master = {o["master_id"]: o for o in overrides if o["kind"] == "replace" and o["master_id"]}
    added = [o for o in overrides if o["kind"] == "add"]

    slots: list[dict] = []
    for master_id, row in master_rows.items():
        if master_id in removed_master_ids:
            continue
        if master_id in replace_by_master:
            override = replace_by_master[master_id]
            merged = dict(row)
            for field in ("day_of_week", "start_time", "end_time", "course_code",
                          "course_name", "session_type", "room", "faculty_name"):
                if override.get(field) is not None:
                    merged[field] = override[field]
            slots.append(_row_to_slot(merged, is_custom=True, override_id=override["id"]))
        else:
            slots.append(_row_to_slot(row))

    for override in added:
        slots.append(_row_to_slot(override, is_custom=True, override_id=override["id"]))

    slots.sort(key=lambda s: (s["day_of_week"], s["start_time"]))
    return {
        "cohort": {"year": year, "sem": sem, "sec": sec},
        "timetable": slots,
    }


def list_my_changes(identity) -> list[dict]:
    if _field(identity, "role") != "student":
        raise TimetableError("Only students have a personal timetable in AURA.")
    overrides = get_overrides(_field(identity, "erp_id"))
    return [
        {
            "id": str(o["id"]),
            "kind": o["kind"],
            "day": day_name(o["day_of_week"]) if o["day_of_week"] is not None else None,
            "course_code": o["course_code"],
            "note": o["note"],
        }
        for o in overrides
    ]


def _find_master_id(year: int, sem: int, sec: str, day_of_week: int,
                     start_time: Optional[str], course_code: Optional[str]) -> Optional[str]:
    rows = get_master_rows(year, sem, sec)
    for row in rows:
        if row["day_of_week"] != day_of_week:
            continue
        if course_code and row["course_code"].lower() != course_code.lower():
            continue
        if start_time and _fmt_time(row["start_time"]) != start_time:
            continue
        return row["id"]
    return None


def apply_change(
    identity,
    kind: str,
    day: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    course_code: Optional[str] = None,
    course_name: Optional[str] = None,
    session_type: Optional[str] = None,
    room: Optional[str] = None,
    faculty_name: Optional[str] = None,
    note: Optional[str] = None,
) -> dict:
    """Writes ONE new override row scoped to identity.erp_id. `kind` is one of
    'replace' | 'add' | 'remove'. Never accepts an erp_id/student_id argument —
    the requester can only ever edit their own timetable."""
    year, sem, sec = _require_cohort(identity)

    if kind not in ("replace", "add", "remove"):
        raise TimetableError("kind must be 'replace', 'add', or 'remove'.")
    if session_type and session_type not in VALID_SESSION_TYPES:
        raise TimetableError("session_type must be 'lecture', 'lab', or 'tutorial'.")

    day_of_week = parse_day(day) if day is not None else None

    master_id = None
    if kind in ("replace", "remove"):
        if day_of_week is None:
            raise TimetableError("Please tell me which day the class you want to change is on.")
        master_id = _find_master_id(year, sem, sec, day_of_week, start_time, course_code)
        if master_id is None:
            raise TimetableError(
                "I couldn't find a matching class on your timetable for that day/time/course — "
                "could you double check the details?"
            )
    elif kind == "add":
        if day_of_week is None or not start_time or not end_time or not course_name:
            raise TimetableError(
                "To add a new class I need at least the day, start time, end time, and course name."
            )

    db_conn.execute(
        """INSERT INTO timetable_overrides
             (erp_id, kind, master_id, day_of_week, start_time, end_time,
              course_code, course_name, session_type, room, faculty_name, note)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            _field(identity, "erp_id"), kind, master_id, day_of_week, start_time, end_time,
            course_code, course_name, session_type, room, faculty_name, note,
        ),
    )

    return get_effective_timetable(identity)


def clear_change(identity, override_id: str) -> dict:
    """Soft-deletes one of the requester's OWN overrides (never another
    student's — the WHERE clause is scoped to erp_id)."""
    if _field(identity, "role") != "student":
        raise TimetableError("Only students have a personal timetable in AURA.")
    db_conn.execute(
        """UPDATE timetable_overrides SET is_active = FALSE, updated_at = now()
           WHERE id = %s AND erp_id = %s""",
        (override_id, _field(identity, "erp_id")),
    )
    return get_effective_timetable(identity)


def find_slots_starting_in(erp_id: str, minutes_from_now: int, now: Optional[datetime.datetime] = None) -> list[dict]:
    """Used by the notification scheduler: does this student have a class
    starting in exactly `minutes_from_now` minutes (rounded to the minute)?"""
    now = now or datetime.datetime.now()
    target = now + datetime.timedelta(minutes=minutes_from_now)
    target_hm = target.strftime("%H:%M")
    target_dow = target.weekday()  # Monday=0 .. Sunday=6, matches our schema

    rows = db_conn.query(
        """SELECT current_year, current_sem, current_sec, role
           FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE""",
        (erp_id,),
    )
    if not rows or rows[0]["role"] != "student":
        return []
    profile = rows[0]
    if profile["current_year"] is None or profile["current_sem"] is None or not profile["current_sec"]:
        return []

    pseudo_identity = _CohortLookup(
        role="student",
        erp_id=erp_id,
        current_year=profile["current_year"],
        current_sem=profile["current_sem"],
        current_sec=profile["current_sec"],
    )
    effective = get_effective_timetable(pseudo_identity)
    return [
        slot for slot in effective["timetable"]
        if slot["day_of_week"] == target_dow and slot["start_time"] == target_hm
    ]
