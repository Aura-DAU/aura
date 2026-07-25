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

    erp_id = _field(identity, "erp_id")
    year = sem = sec = None

    if erp_id:
        try:
            rows = db_conn.query(
                "SELECT current_year, current_sem, current_sec, email FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
                (erp_id,),
            )
            if rows:
                r = rows[0]
                year = r.get("current_year")
                sem = r.get("current_sem")
                sec = r.get("current_sec")

                # If still missing in DB, infer from email
                if (year is None or sem is None or not sec) and r.get("email"):
                    from api.routes.identity_routes import _infer_role_and_cohort
                    inferred = _infer_role_and_cohort(r["email"])
                    if inferred["role"] == "student":
                        year = year if year is not None else inferred["current_year"]
                        sem = sem if sem is not None else inferred["current_sem"]
                        sec = sec if sec else inferred["current_sec"]
        except Exception:
            pass

    # Fallback to identity object if DB fields were empty
    if year is None: year = _field(identity, "current_year")
    if sem is None: sem = _field(identity, "current_sem")
    if not sec: sec = _field(identity, "current_sec")

    if year is None or sem is None or not sec:
        raise TimetableError(
            "Your year/semester/section isn't set up yet in AURA — please update "
            "your profile or contact the AURA administrator."
        )
    return int(year), int(sem), str(sec)


def get_master_rows(year: int, sem: int, sec: str) -> list[dict]:
    return db_conn.query(
        """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name,
                  course_type
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
        "course_type": row.get("course_type", ""),
        "is_custom": is_custom,
    }


def _is_elective(course_type: str) -> bool:
    """Returns True if the course_type indicates an elective."""
    return bool(course_type) and "elective" in course_type.lower()


def _get_selected_elective_ids(erp_id: str) -> set[str]:
    """Returns the set of master_ids the student has selected as their electives.
    Empty set means no preferences saved yet."""
    rows = db_conn.query(
        "SELECT master_id FROM student_elective_selections WHERE erp_id = %s",
        (erp_id,),
    )
    return {str(r["master_id"]) for r in rows}


def has_elective_selections(erp_id: str) -> bool:
    """Returns True if the student has saved at least one elective selection."""
    rows = db_conn.query(
        "SELECT 1 FROM student_elective_selections WHERE erp_id = %s LIMIT 1",
        (erp_id,),
    )
    return len(rows) > 0


def get_all_elective_rows(year: int, sem: int) -> list[dict]:
    """Returns elective-type master rows offered to a specific (year, sem) —
    NOT every elective in the whole database. Electives are commonly pooled
    across all sections of the same year+sem (matching the source
    timetable), so this intentionally does not filter by `sec`.

    This scoping matters: without it, a student's course_code could
    resolve to a master row belonging to a completely different cohort
    (different year/semester), and get_effective_timetable would then
    merge that unrelated class straight into their own timetable."""
    return db_conn.query(
        """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name,
                  course_type
           FROM timetable_master
           WHERE (course_type ILIKE '%%Elective%%' OR program ILIKE '%%Elective%%')
             AND year = %s AND sem = %s
           ORDER BY course_code, day_of_week, start_time""",
        (year, sem),
    )


def get_effective_timetable(identity) -> dict:
    """Returns {"cohort": {...}, "timetable": [slot, ...], "electives_configured": bool}
    sorted by day/time, for the identity's own (year, sem, sec), merged with
    their overrides and selected electives.
    """
    year, sem, sec = _require_cohort(identity)
    erp_id = _field(identity, "erp_id")
    master_rows = {row["id"]: row for row in get_master_rows(year, sem, sec)}
    overrides = get_overrides(erp_id)

    # Elective filtering & inclusion
    selected_ids = _get_selected_elective_ids(erp_id)
    electives_configured = len(selected_ids) > 0
    if electives_configured:
        all_electives = get_all_elective_rows(year, sem)
        for erow in all_electives:
            if str(erow["id"]) in selected_ids:
                master_rows[erow["id"]] = erow

    removed_master_ids = {o["master_id"] for o in overrides if o["kind"] == "remove" and o["master_id"]}
    replace_by_master = {o["master_id"]: o for o in overrides if o["kind"] == "replace" and o["master_id"]}
    added = [o for o in overrides if o["kind"] == "add"]

    slots: list[dict] = []
    for master_id, row in master_rows.items():
        if master_id in removed_master_ids:
            continue

        # Filter electives: skip if student has configured preferences
        # and this elective is NOT one they selected
        if electives_configured and _is_elective(row.get("course_type", "")):
            if str(master_id) not in selected_ids:
                continue

        if master_id in replace_by_master:
            override = replace_by_master[master_id]
            merged = dict(row)
            for fld in ("day_of_week", "start_time", "end_time", "course_code",
                          "course_name", "session_type", "room", "faculty_name"):
                if override.get(fld) is not None:
                    merged[fld] = override[fld]
            slots.append(_row_to_slot(merged, is_custom=True, override_id=override["id"]))
        else:
            slots.append(_row_to_slot(row))

    for override in added:
        slots.append(_row_to_slot(override, is_custom=True, override_id=override["id"]))

    slots.sort(key=lambda s: (s["day_of_week"], s["start_time"]))
    return {
        "cohort": {"year": year, "sem": sem, "sec": sec},
        "electives_configured": electives_configured,
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


# -- Faculty timetable (read-only, across all batches) -------------------------


def get_faculty_rows(faculty_name: str) -> list[dict]:
    """Get all master rows where faculty_name matches (case-insensitive).
    Also matches combined faculty like 'SS/VS' when queried with 'SS' or 'VS'."""
    return db_conn.query(
        """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name,
                  batch_raw, branch, program, credits, course_type
           FROM timetable_master
           WHERE UPPER(faculty_name) = UPPER(%s)
              OR UPPER(faculty_name) LIKE '%%' || UPPER(%s) || '/%%'
              OR UPPER(faculty_name) LIKE '%%/' || UPPER(%s) || '%%'
           ORDER BY day_of_week, start_time""",
        (faculty_name, faculty_name, faculty_name),
    )


def get_faculty_timetable(identity) -> dict:
    """Returns the full weekly teaching schedule for a faculty member.
    Queries all classes across every batch/year/section where this
    faculty member is listed as the instructor."""
    role = _field(identity, "role")
    if role != "faculty":
        raise TimetableError("This tool is only available to faculty members.")

    faculty_name = _field(identity, "faculty_initials") or _field(identity, "erp_id")
    if not faculty_name:
        raise TimetableError(
            "Your faculty identifier is not set up in AURA. "
            "Please contact the administrator."
        )

    rows = get_faculty_rows(faculty_name)
    slots = []
    for row in rows:
        slot = _row_to_slot(row)
        slot["batch"] = row.get("batch_raw", "")
        slot["branch"] = row.get("branch", "")
        slot["program"] = row.get("program", "")
        slot["credits"] = row.get("credits", "")
        slot["course_type"] = row.get("course_type", "")
        slots.append(slot)

    return {
        "faculty": faculty_name,
        "total_classes_per_week": len(slots),
        "timetable": slots,
    }


# -- Elective selection -------------------------------------------------------


def get_available_electives(identity) -> dict:
    """Returns all elective-type courses for the student's cohort, with a
    `selected` flag indicating whether the student has chosen each one.

    Courses are grouped by course_code so the student sees each elective
    once (not once per time slot). The individual time slots are nested
    under each course for reference.
    """
    year, sem, sec = _require_cohort(identity)
    erp_id = _field(identity, "erp_id")
    selected_ids = _get_selected_elective_ids(erp_id)
    electives_configured = len(selected_ids) > 0

    elective_rows = get_all_elective_rows(year, sem)
    # Group by course_code
    courses: dict[str, dict] = {}
    for row in elective_rows:
        code = row["course_code"]
        mid = str(row["id"])
        if code not in courses:
            courses[code] = {
                "course_code": code,
                "course_name": row["course_name"],
                "course_type": row.get("course_type", ""),
                "selected": mid in selected_ids if electives_configured else False,
                "master_ids": [],
                "slots": [],
            }
        courses[code]["master_ids"].append(mid)
        # If any slot for this course is selected, mark the course as selected
        if electives_configured and mid in selected_ids:
            courses[code]["selected"] = True
        courses[code]["slots"].append({
            "master_id": mid,
            "day": day_name(row["day_of_week"]),
            "day_of_week": row["day_of_week"],
            "start_time": _fmt_time(row["start_time"]),
            "end_time": _fmt_time(row["end_time"]),
            "faculty_name": row.get("faculty_name", ""),
            "room": row.get("room", ""),
        })

    return {
        "cohort": {"year": year, "sem": sem, "sec": sec},
        "electives_configured": electives_configured,
        "electives": list(courses.values()),
    }


def save_elective_selections(identity, course_codes: list[str]) -> dict:
    """Saves the student's elective choices. Accepts a list of course_codes
    (not master_ids) -- all master slots for each selected course_code are
    automatically included.

    Replaces any previous selections entirely (idempotent).
    """
    year, sem, sec = _require_cohort(identity)
    erp_id = _field(identity, "erp_id")

    if not course_codes:
        raise TimetableError("Please select at least one elective course.")

    # Resolve course_codes to master_ids — scoped to the student's own
    # (year, sem) so they can only select electives actually offered to
    # their cohort, never a course_code that happens to also exist in a
    # different year/semester's offering.
    elective_rows = get_all_elective_rows(year, sem)

    code_set = {c.strip().upper() for c in course_codes}
    matched_ids = []
    matched_codes = set()
    for row in elective_rows:
        if row["course_code"].upper() in code_set:
            matched_ids.append(str(row["id"]))
            matched_codes.add(row["course_code"].upper())

    unmatched = code_set - matched_codes
    if unmatched:
        raise TimetableError(
            f"These course codes are not available as electives: "
            f"{', '.join(sorted(unmatched))}. Use get_available_electives to see valid options."
        )

    # Atomic replace: delete old, insert new
    db_conn.execute(
        "DELETE FROM student_elective_selections WHERE erp_id = %s",
        (erp_id,),
    )
    for mid in matched_ids:
        db_conn.execute(
            "INSERT INTO student_elective_selections (erp_id, master_id) VALUES (%s, %s)",
            (erp_id, mid),
        )

    return {
        "status": "saved",
        "selected_courses": sorted(matched_codes),
        "total_slots": len(matched_ids),
    }


def update_student_cohort(identity, year: Optional[int] = None, sem: Optional[int] = None, sec: Optional[str] = None) -> dict:
    """Updates the student's cohort (year, semester, section) in user_identity_map."""
    role = _field(identity, "role")
    if role != "student":
        raise TimetableError("Only students can set their cohort.")
    erp_id = _field(identity, "erp_id")

    cur_year = _field(identity, "current_year")
    cur_sem = _field(identity, "current_sem")
    cur_sec = _field(identity, "current_sec") or "A"

    new_year = int(year) if year is not None else cur_year
    new_sem = int(sem) if sem is not None else cur_sem
    new_sec = str(sec).strip().upper() if sec else cur_sec

    if new_year is None or new_sem is None:
        raise TimetableError(
            "I don't know your current year and semester yet, so I can't fill in what you didn't "
            "specify — please tell me your year, semester, and section together this first time."
        )

    # Validate against timetable_master
    check = db_conn.query(
        "SELECT 1 FROM timetable_master WHERE year = %s AND sem = %s AND sec = %s LIMIT 1",
        (new_year, new_sem, new_sec),
    )
    if not check:
        raise TimetableError(f"No timetable found for Year {new_year}, Semester {new_sem}, Section '{new_sec}'.")

    db_conn.execute(
        "UPDATE user_identity_map SET current_year = %s, current_sem = %s, current_sec = %s WHERE erp_id = %s",
        (new_year, new_sem, new_sec, erp_id),
    )

    if isinstance(identity, dict):
        identity["current_year"] = new_year
        identity["current_sem"] = new_sem
        identity["current_sec"] = new_sec
    else:
        setattr(identity, "current_year", new_year)
        setattr(identity, "current_sem", new_sem)
        setattr(identity, "current_sec", new_sec)

    return {
        "status": "updated",
        "cohort": {"year": new_year, "sem": new_sem, "sec": new_sec},
        "message": f"Successfully updated your cohort to Year {new_year}, Semester {new_sem}, Section {new_sec}.",
        "timetable": get_effective_timetable(identity),
    }

