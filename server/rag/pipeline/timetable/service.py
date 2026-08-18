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
import logging
import os
import re
from dataclasses import dataclass
from typing import Optional

import db.connection as db_conn

logger = logging.getLogger("aura.timetable.service")

# The active semester's timetable_master.semester_label. Every real import
# (import_timetable_xlsx.py --semester "...") stamps this on every row it
# writes; historical/other-semester imports and legacy seed data
# (server/scripts/load_timetable.sql never sets semester_label at all, so
# those rows are NULL) are excluded by the exact-match filter this enables.
#
# Without this, get_master_rows/get_effective_timetable/get_all_elective_rows
# match purely on (year, sem, sec) and silently merge every semester's data
# ever imported for that cohort into one view -- this is what caused Section
# A and B (and stale/demo rows) to show up mixed together. Must be set in
# the backend's .env on every deploy where the semester changes.
CURRENT_SEMESTER_LABEL = os.getenv("CURRENT_SEMESTER_LABEL", "").strip()
if not CURRENT_SEMESTER_LABEL:
    logger.warning(
        "CURRENT_SEMESTER_LABEL is not set - timetable queries will NOT filter "
        "by semester_label and may return rows from stale/demo imports. Set it "
        "in the backend's .env to e.g. 'Autumn 2026-27'."
    )

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VALID_SESSION_TYPES = {"lecture", "lab", "tutorial"}

# BUG-02 fix: start_time/end_time arrive as raw strings from LLM tool-call
# arguments. Without a format check here, malformed values (e.g. "8:00 AM",
# "25:00") reach the DB and either raise an unhandled psycopg2 exception
# (leaking a DB traceback to the LLM/client) or silently misbehave.
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$")


def _validate_time(t: Optional[str], field_name: str) -> Optional[str]:
    if t is None:
        return None
    if not _TIME_RE.match(t):
        raise TimetableError(f"{field_name} must be in 24-hour HH:MM format (e.g. '09:00').")
    return t


def _to_minutes(t: str) -> int:
    parts = t.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _slots_overlap(start_a: str, end_a: str, start_b: str, end_b: str) -> bool:
    return _to_minutes(start_a) < _to_minutes(end_b) and _to_minutes(start_b) < _to_minutes(end_a)


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
    """Raised for user-facing validation problems (bad day name, missing cohort, etc.).

    API-03 fix: carries an explicit `status_code` (default 400, the common
    case — bad input / not-yet-configured state) so route handlers can map
    it correctly instead of blanket-returning 409 for everything. Pass
    status_code=404 for "couldn't find the thing you're referring to" and
    status_code=409 for a genuine resource conflict (e.g. overlapping slot).
    """

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class TimetableForbiddenError(TimetableError):
    """Role-mismatch errors (e.g. a faculty-only tool called by a student)."""

    def __init__(self, message: str):
        super().__init__(message, status_code=403)


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


def _resolve_faculty_initials(identity) -> Optional[str]:
    """Best-effort resolution of a faculty member's short initials (e.g.
    'AM1'), used to look up their teaching schedule in timetable_master.
    Mirrors _resolve_dept() above: the REST /timetable/me path already
    carries faculty_initials on the JWT, but the chat/agent path keeps its
    internal JWT deliberately minimal (role/erp_id/department/email only),
    so this falls back to a DB lookup — and, if that row itself doesn't
    have it cached yet, to re-inferring it from FACULTY_INITIALS the same
    way resolve_identity() does at login. Never raises: a faculty member
    whose initials can't be determined simply gets no personal schedule
    rather than an error."""
    initials = _field(identity, "faculty_initials")
    if initials:
        return str(initials)

    erp_id = _field(identity, "erp_id")
    email = _field(identity, "email")

    try:
        if erp_id:
            rows = db_conn.query(
                "SELECT faculty_initials, email FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
                (erp_id,),
            )
            if rows:
                r = rows[0]
                if r.get("faculty_initials"):
                    return str(r["faculty_initials"])
                email = email or r.get("email")
    except Exception:
        pass

    if email:
        try:
            from api.routes.identity_routes import _infer_role_and_cohort
            inferred = _infer_role_and_cohort(email)
            if inferred.get("faculty_initials"):
                return str(inferred["faculty_initials"])
        except Exception:
            pass

    return None


def _resolve_dept(identity) -> Optional[str]:
    """Best-effort resolution of the student's branch/department (e.g. 'ICT',
    'MnC', 'ICTCS'), used to keep two different branches that happen to share
    the same (year, sem, sec) label — e.g. both have a 'Section A' — from
    being merged into a single combined timetable. Never raises: a student
    whose department can't be determined simply gets the old unfiltered
    behaviour rather than an error."""
    dept = _field(identity, "dept")
    if dept:
        return str(dept)

    erp_id = _field(identity, "erp_id")
    if not erp_id:
        return None

    try:
        rows = db_conn.query(
            "SELECT dept, email FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
            (erp_id,),
        )
        if rows:
            r = rows[0]
            if r.get("dept"):
                return str(r["dept"])
            email = r.get("email") or f"{erp_id}@dau.ac.in"
            from api.routes.identity_routes import _infer_role_and_cohort
            inferred = _infer_role_and_cohort(email)
            if inferred.get("dept"):
                return str(inferred["dept"])
    except Exception:
        pass

    try:
        from api.routes.identity_routes import _infer_role_and_cohort
        inferred = _infer_role_and_cohort(f"{erp_id}@dau.ac.in")
        if inferred.get("dept"):
            return str(inferred["dept"])
    except Exception:
        pass

    return None


def _narrow_by_dept(rows: list[dict], dept: Optional[str]) -> list[dict]:
    """Soft-filters master rows down to just this student's branch/programme,
    e.g. so an ICT student doesn't see MnC's classes mixed into their own
    timetable just because both cohorts share the same (year, sem, sec)
    label. Mirrors get_timetable_for_cohort's branch narrowing: only applies
    when it's known AND actually narrows to a non-empty set, so rows with
    NULL branch/program (not backfilled yet, see migration 007) keep showing
    everything rather than being filtered down to nothing."""
    needle = (dept or "").strip().lower()
    if not needle or not rows:
        return rows
    out = []
    for r in rows:
        branch = (r.get("branch") or "").strip()
        program = (r.get("program") or "").strip()
        if not branch and not program:
            # Untagged rows (e.g. the 2nd/3rd-year Core batches called out
            # above) are ambiguous by design, never confirmed to belong to a
            # different dept — always keep them regardless of whether other
            # rows in this set happen to match `dept`. Previously this used
            # "narrowed if narrowed else rows", which only guarded the
            # all-empty case: a single matching row anywhere in the set was
            # enough to silently drop every untagged Core row alongside it.
            out.append(r)
            continue
        if needle in branch.lower() or needle in program.lower():
            out.append(r)
    return out


def _normalize_dept(value: Optional[str]) -> str:
    """'ICT-CS' / 'ICT_CS' / 'ict cs' all normalize to 'ICTCS' so dept values
    coming from different places (email-inferred 'ICTCS', curated doc labels
    'ICT-CS', DB free text, etc.) compare equal."""
    return re.sub(r"[^A-Z0-9]", "", (value or "").upper())


# Course-code → branch(es) lookup, hand-verified against the curated
# per-branch timetable docs in data/academics/timetable/*.md (produced by
# cross-referencing the raw combined sheet against the registrar's course
# structure). The source spreadsheet's "Core" batch blocks for 2nd/3rd year
# don't tag each row with a branch at all — course codes are the only signal
# — so this map exists to fill that gap for the specific codes that were
# actually confirmed. Deliberately NOT exhaustive: a course_code with no
# entry here is left unfiltered (shown to every branch), matching the
# curated docs' own approach of flagging genuine ambiguity instead of
# guessing. Extend this as more cohorts/years get verified.
#
# Year 3 / Sem 5 (see ICT_3rd_Yr_Sem5.md, ICT-CS_3rd_Yr_Sem5.md,
# MNC_3rd_Yr_Sem5.md, EVD_3rd_Yr_Sem5.md):
#   - IT304/IT314/CT303 are the shared ICT + ICT-CS core (ICT-CS only
#     diverges starting Sem 4, and CS374 is its one added specialization
#     course this semester).
#   - MC311-314 are MnC-only; ED311/ED312 + HM116 are EVD-only. MC314 and
#     HM116 are the SAME Principles of Economics class recorded under two
#     different codes for MnC vs EVD — not two separate classes.
# Year 2 / Sem 3 (see ICT_and_ICT-CS_2nd_Yr_Sem3.md, MNC_2nd_Yr_Sem3.md,
# EVD_2nd_Yr_Sem3.md): ICT and ICT-CS are still on an identical curriculum
# this semester, so both map to the same course codes (that's correct, not
# a mixing bug). HM216 is intentionally left OUT of this map — it's a large
# shared lecture taken by all four branches, just split into two
# room-capacity sections, so it should stay visible to everyone.
COURSE_BRANCH_MAP: dict[str, set[str]] = {
    # Year 3 / Sem 5
    "IT304": {"ICT", "ICTCS"},
    "IT314": {"ICT", "ICTCS"},
    "CT303": {"ICT", "ICTCS"},
    "CS374": {"ICTCS"},
    "MC311": {"MNC"}, "MC312": {"MNC"}, "MC313": {"MNC"}, "MC314": {"MNC"},
    "ED311": {"EVD"}, "ED312": {"EVD"}, "HM116": {"EVD"},
    # Year 2 / Sem 3
    "SC223": {"ICT", "ICTCS"}, "IT227": {"ICT", "ICTCS"},
    "CT204": {"ICT", "ICTCS"}, "IT216": {"ICT", "ICTCS"},
    "MC211": {"MNC"}, "MC212": {"MNC"}, "MC213": {"MNC"},
    "MC214": {"MNC"}, "MC216": {"MNC"},
    "ED211": {"EVD"}, "ED212": {"EVD"}, "ED213": {"EVD"}, "ED214": {"EVD"},
}


def _narrow_by_course_branch_map(rows: list[dict], dept: Optional[str]) -> list[dict]:
    """Drops rows whose course_code is confirmed (via COURSE_BRANCH_MAP) to
    belong to a *different* branch than the student's. Unknown course codes
    and unknown student dept both pass through unfiltered — this only acts
    where we have a verified answer, never a guess."""
    dept_norm = _normalize_dept(dept)
    if not dept_norm:
        return rows
    out = []
    for row in rows:
        branches = COURSE_BRANCH_MAP.get((row.get("course_code") or "").strip().upper())
        if branches and dept_norm not in branches:
            continue
        out.append(row)
    return out


def _exclude_electives(rows: list[dict]) -> list[dict]:
    """Electives must only ever enter the timetable through the explicit
    selection step below (get_all_elective_rows + selected_ids) — never
    through the general per-cohort query. Without this, an elective master
    row that happens to share the student's (year, sem, sec) — including
    the 'sec is blank' rows the common-fallback query matches — leaks into
    every student's timetable regardless of whether they've picked it."""
    return [row for row in rows if not _is_elective(row.get("course_type", ""))]
def _require_cohort(identity) -> tuple[int, int, str]:
    role = _field(identity, "role")
    if role != "student":
        raise TimetableForbiddenError("Only students have a personal timetable in AURA.")

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

    # If still missing, infer directly from erp_id
    if (year is None or sem is None or not sec) and erp_id:
        try:
            from api.routes.identity_routes import _infer_role_and_cohort
            inferred = _infer_role_and_cohort(f"{erp_id}@dau.ac.in")
            if inferred["role"] == "student":
                year = year if year is not None else inferred["current_year"]
                sem = sem if sem is not None else inferred["current_sem"]
                sec = sec if sec else inferred["current_sec"]
        except Exception:
            pass

    # All resolution paths exhausted — missing cohort is a hard error.
    if year is None or sem is None or not sec:
        raise TimetableError(
            "Your year, semester, and section are not set up in AURA yet. "
            "Please contact your administrator or set your cohort before using timetable features."
        )

    return int(year), int(sem), str(sec)


def get_master_rows(year: int, sem: int, sec: str, dept: Optional[str] = None, lab_group: Optional[str] = None) -> list[dict]:
    if CURRENT_SEMESTER_LABEL:
        rows = db_conn.query(
            """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                      course_code, course_name, session_type, room, faculty_name,
                      course_type, branch, program
               FROM timetable_master
               WHERE year = %s AND sem = %s AND (sec IS NULL OR sec = '' OR sec = %s)
                 AND (lab_group IS NULL OR lab_group = '' OR lab_group = %s)
                 AND semester_label = %s
               ORDER BY day_of_week, start_time""",
            (year, sem, sec, lab_group or "", CURRENT_SEMESTER_LABEL),
        )
    else:
        rows = db_conn.query(
            """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                      course_code, course_name, session_type, room, faculty_name,
                      course_type, branch, program
               FROM timetable_master
               WHERE year = %s AND sem = %s AND (sec IS NULL OR sec = '' OR sec = %s)
                 AND (lab_group IS NULL OR lab_group = '' OR lab_group = %s)
               ORDER BY day_of_week, start_time""",
            (year, sem, sec, lab_group or ""),
        )
    return _narrow_by_dept(rows, dept)


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
    # BUG-03 support: expose the underlying master_id so overlap detection
    # can exclude a slot from colliding with the very master row it's
    # replacing. An override row (fetched via get_overrides) already carries
    # its own "master_id" column (None for a plain 'add'); a plain master
    # row, or a replace-merged dict copied from one, has no "master_id" key
    # and its "id" field IS the master id.
    master_id_val = row.get("master_id") if "master_id" in row else row.get("id")

    return {
        "id": str(override_id or row["id"]),
        "master_id": str(master_id_val) if master_id_val else None,
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
    if CURRENT_SEMESTER_LABEL:
        return db_conn.query(
            """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                      course_code, course_name, session_type, room, faculty_name,
                      course_type
               FROM timetable_master
               WHERE (course_type ILIKE '%%Elective%%' OR program ILIKE '%%Elective%%')
                 AND year = 0 AND sem = 0
                 AND semester_label = %s
               ORDER BY course_code, day_of_week, start_time""",
            (CURRENT_SEMESTER_LABEL,),
        )
    return db_conn.query(
        """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                  course_code, course_name, session_type, room, faculty_name,
                  course_type
           FROM timetable_master
           WHERE (course_type ILIKE '%%Elective%%' OR program ILIKE '%%Elective%%')
             AND year = 0 AND sem = 0
           ORDER BY course_code, day_of_week, start_time""",
    )


def get_effective_timetable(identity) -> dict:
    """Returns {"cohort": {...}, "timetable": [slot, ...], "electives_configured": bool}
    sorted by day/time, for the identity's own (year, sem, sec), merged with
    their overrides and selected electives.
    """
    is_common = False
    try:
        year, sem, sec = _require_cohort(identity)
    except TimetableError as e:
        # Student doesn't have cohort setup yet: let's try to infer year/sem from ERP ID or email
        # so we can show a default common timetable of their year/semester.
        erp_id = _field(identity, "erp_id")
        role = _field(identity, "role")
        if role != "student":
            raise
        
        # Try to resolve year/sem/sec from user_identity_map or infer from erp_id
        year = _field(identity, "current_year")
        sem = _field(identity, "current_sem")
        sec = _field(identity, "current_sec")
        
        if (year is None or sem is None) and erp_id:
            try:
                from api.routes.identity_routes import _infer_role_and_cohort
                inferred = _infer_role_and_cohort(f"{erp_id}@dau.ac.in")
                if inferred["role"] == "student":
                    year = year if year is not None else inferred["current_year"]
                    sem = sem if sem is not None else inferred["current_sem"]
                    sec = sec if sec else inferred["current_sec"]
            except Exception:
                pass
        
        # Fallback to year 1 if not inferrable
        if year is None: year = 1
        if sem is None: sem = 1
        
        is_common = True
        sec = None

    erp_id = _field(identity, "erp_id")
    dept = _resolve_dept(identity)
    lab_group = _field(identity, "current_lab_group")

    if sec is None:
        # Fetch common courses (where sec is null/empty or default to 'A' as representative).
        # Narrowed by dept (when known) so e.g. an ICT student doesn't also get
        # MnC's classes just because both cohorts happen to use section 'A'.
        if CURRENT_SEMESTER_LABEL:
            common_rows = db_conn.query(
                """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                          course_code, course_name, session_type, room, faculty_name,
                          course_type, branch, program
                   FROM timetable_master
                   WHERE year = %s AND sem = %s AND (sec IS NULL OR sec = '' OR sec = 'A')
                     AND (lab_group IS NULL OR lab_group = '' OR lab_group = %s)
                     AND semester_label = %s
                   ORDER BY day_of_week, start_time""",
                (year, sem, lab_group or "", CURRENT_SEMESTER_LABEL),
            )
        else:
            common_rows = db_conn.query(
                """SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                          course_code, course_name, session_type, room, faculty_name,
                          course_type, branch, program
                   FROM timetable_master
                   WHERE year = %s AND sem = %s AND (sec IS NULL OR sec = '' OR sec = 'A')
                     AND (lab_group IS NULL OR lab_group = '' OR lab_group = %s)
                   ORDER BY day_of_week, start_time""",
                (year, sem, lab_group or ""),
            )
        common_rows = _narrow_by_dept(common_rows, dept)
        common_rows = _narrow_by_course_branch_map(common_rows, dept)
        common_rows = _exclude_electives(common_rows)
        master_rows = {row["id"]: row for row in common_rows}
        is_common = True
    else:
        rows = get_master_rows(year, sem, sec, dept, lab_group)
        rows = _narrow_by_course_branch_map(rows, dept)
        rows = _exclude_electives(rows)
        master_rows = {row["id"]: row for row in rows}
        
    overrides = get_overrides(erp_id) if erp_id else []

    # Elective filtering & inclusion
    selected_ids = _get_selected_elective_ids(erp_id) if erp_id else set()
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
        "cohort": {"year": year, "sem": sem, "sec": sec or "A"},
        "electives_configured": electives_configured,
        "timetable": slots,
        "is_common": is_common,
        "needs_configuration": is_common or not electives_configured
    }



def list_my_changes(identity) -> list[dict]:
    if _field(identity, "role") != "student":
        raise TimetableForbiddenError("Only students have a personal timetable in AURA.")
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

    # BUG-02 fix: validate time format before it ever reaches the DB.
    start_time = _validate_time(start_time, "start_time")
    end_time = _validate_time(end_time, "end_time")
    if start_time and end_time and _to_minutes(end_time) <= _to_minutes(start_time):
        raise TimetableError("end_time must be after start_time.")

    day_of_week = parse_day(day) if day is not None else None

    master_id = None
    if kind in ("replace", "remove"):
        if day_of_week is None:
            raise TimetableError("Please tell me which day the class you want to change is on.")
        master_id = _find_master_id(year, sem, sec, day_of_week, start_time, course_code)
        if master_id is None:
            raise TimetableError(
                "I couldn't find a matching class on your timetable for that day/time/course — "
                "could you double check the details?",
                status_code=404,
            )
    elif kind == "add":
        if day_of_week is None or not start_time or not end_time or not course_name:
            raise TimetableError(
                "To add a new class I need at least the day, start time, end time, and course name."
            )

    # BUG-03 fix: for 'add' and 'replace', reject a slot that overlaps an
    # existing slot on the same day in the student's *effective* timetable
    # (skipping the slot being replaced itself), so a student can't end up
    # with two classes at the same time.
    if kind in ("add", "replace") and day_of_week is not None and start_time and end_time:
        effective = get_effective_timetable(identity)
        for slot in effective["timetable"]:
            if slot["day_of_week"] != day_of_week:
                continue
            if kind == "replace" and master_id is not None and slot.get("master_id") == master_id:
                continue
            if _slots_overlap(start_time, end_time, slot["start_time"], slot["end_time"]):
                raise TimetableError(
                    f"That overlaps with {slot.get('course_code') or 'an existing class'} "
                    f"({slot['start_time']}\u2013{slot['end_time']}) on {day_name(day_of_week)}.",
                    status_code=409,
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
        raise TimetableForbiddenError("Only students have a personal timetable in AURA.")
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
        raise TimetableForbiddenError("This tool is only available to faculty members.")

    faculty_name = _resolve_faculty_initials(identity) or _field(identity, "erp_id")
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


# -- Any-cohort timetable lookup (read-only, not scoped to the requester) -----


def get_timetable_for_cohort(
    year: Optional[int] = None,
    sem: Optional[int] = None,
    sec: Optional[str] = None,
    branch: Optional[str] = None,
    program: Optional[str] = None,
) -> dict:
    """Read-only lookup of ANY cohort's master timetable by semester/section
    (+ optional branch/program), for chat queries like "give me the timetable
    of BTech ICT 3rd sem sec A" that are NOT about the requester's own
    schedule. Unlike get_effective_timetable, this never applies a specific
    student's personal overrides or elective picks -- it's the plain master
    schedule for whichever cohort was asked about.

    `sec` defaults to 'A' when omitted, matching the rest of the timetable
    feature's default section. `branch`/`program` are a soft filter only:
    timetable_master.branch/program can be NULL on rows imported before
    those columns existed (see migration 007), so a non-matching/empty
    result after filtering falls back to the unfiltered sem+sec rows rather
    than reporting "not found" over a cosmetic label mismatch.
    """
    if sem is None and year is not None:
        # Infer current semester from the current month:
        # Autumn (Jul-Dec) -> odd semesters; Spring (Jan-Jun) -> even semesters.
        import datetime
        current_month = datetime.datetime.now().month
        if 7 <= current_month <= 12:
            sem = year * 2 - 1
        else:
            sem = year * 2

    if sem is None:
        raise TimetableError(
            "Please tell me the semester (or academic year) you'd like the timetable for."
        )

    sec_norm = (sec or "A").strip().upper()

    where = ["sem = %s", "sec = %s"]
    params: list = [int(sem), sec_norm]
    if year is not None:
        where.append("year = %s")
        params.append(int(year))

    rows = db_conn.query(
        f"""SELECT id, year, sem, sec, day_of_week, start_time, end_time,
                   course_code, course_name, session_type, room, faculty_name,
                   course_type, branch, program
            FROM timetable_master
            WHERE {' AND '.join(where)}
            ORDER BY day_of_week, start_time""",
        tuple(params),
    )

    needle = (branch or program or "").strip().lower()
    if needle and rows:
        narrowed = [
            r for r in rows
            if needle in (r.get("branch") or "").lower() or needle in (r.get("program") or "").lower()
        ]
        if narrowed:
            rows = narrowed

    if not rows:
        where_desc = f"Semester {sem}, Section '{sec_norm}'"
        if year is not None:
            where_desc = f"Year {year}, " + where_desc
        if branch:
            where_desc += f", Branch '{branch}'"
        raise TimetableError(
            f"I couldn't find a timetable for {where_desc}. "
            "Double check the year/semester, branch, and section.",
            status_code=404,
        )

    slots = [_row_to_slot(r) for r in rows]
    slots.sort(key=lambda s: (s["day_of_week"], s["start_time"]))
    resolved_year = rows[0].get("year", year)
    resolved_branch = next((r.get("branch") for r in rows if r.get("branch")), branch)

    return {
        "cohort": {
            "year": resolved_year,
            "sem": int(sem),
            "sec": sec_norm,
            "branch": resolved_branch,
        },
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
                "slots": [],
            }
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

    # BUG-09 fix: an empty course_codes list is now a valid "reset" request —
    # it clears any saved selections and reverts the student to the
    # pre-configuration state where every elective is shown, rather than
    # being rejected outright.
    if not course_codes:
        with db_conn.get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM student_elective_selections WHERE erp_id = %s",
                    (erp_id,),
                )
        return {
            "status": "reset",
            "selected_courses": [],
            "total_slots": 0,
            "timetable": get_effective_timetable(identity),
        }

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

    # BUG-01 fix: DELETE + N x INSERT must be one transaction, not N+1
    # separate db_conn.execute() calls (each of which checks out its own
    # connection and commits independently). A single get_conn() block
    # keeps the replace atomic — a concurrent reader never observes a
    # window with zero electives, and a crash mid-write rolls back fully
    # instead of losing the student's prior selections.
    with db_conn.get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM student_elective_selections WHERE erp_id = %s",
                (erp_id,),
            )
            for mid in matched_ids:
                cur.execute(
                    "INSERT INTO student_elective_selections (erp_id, master_id) VALUES (%s, %s)",
                    (erp_id, mid),
                )

    # API-02 fix: return the updated effective timetable inline so the
    # frontend doesn't need a second round trip to /timetable/me.
    return {
        "status": "saved",
        "selected_courses": sorted(matched_codes),
        "total_slots": len(matched_ids),
        "timetable": get_effective_timetable(identity),
    }


def update_student_cohort(
    identity: Union[Identity, Dict[str, Any]],
    year: Optional[int] = None,
    sem: Optional[int] = None,
    sec: Optional[str] = None,
    lab_group: Optional[str] = None,
) -> Dict[str, Any]:
    """Updates the student's cohort (year, semester, section) in user_identity_map."""
    role = _field(identity, "role")
    if role != "student":
        raise TimetableForbiddenError("Only students can set their cohort.")
    erp_id = _field(identity, "erp_id")

    cur_year = _field(identity, "current_year")
    cur_sem = _field(identity, "current_sem")
    cur_sec = _field(identity, "current_sec") or "A"
    cur_lab = _field(identity, "current_lab_group")

    new_year = int(year) if year is not None else cur_year
    new_sem = int(sem) if sem is not None else cur_sem
    new_sec = str(sec).strip().upper() if sec else cur_sec
    new_lab = str(lab_group).strip().upper() if lab_group else cur_lab

    if new_year is None or new_sem is None:
        raise TimetableError(
            "I don't know your current year and semester yet, so I can't fill in what you didn't "
            "specify — please tell me your year, semester, and section together this first time."
        )

    # Validate against timetable_master
    # Note: we don't strictly require lab_group to match because they might not have a lab group selected yet
    if CURRENT_SEMESTER_LABEL:
        check = db_conn.query(
            "SELECT 1 FROM timetable_master WHERE year = %s AND sem = %s AND sec = %s "
            "AND semester_label = %s LIMIT 1",
            (new_year, new_sem, new_sec, CURRENT_SEMESTER_LABEL),
        )
    else:
        check = db_conn.query(
            "SELECT 1 FROM timetable_master WHERE year = %s AND sem = %s AND sec = %s LIMIT 1",
            (new_year, new_sem, new_sec),
        )
    if not check:
        raise TimetableError(
            f"No timetable found for Year {new_year}, Semester {new_sem}, Section '{new_sec}'.",
            status_code=404,
        )

    db_conn.execute(
        "UPDATE user_identity_map SET current_year = %s, current_sem = %s, current_sec = %s, current_lab_group = %s WHERE erp_id = %s",
        (new_year, new_sem, new_sec, new_lab, erp_id),
    )

    if isinstance(identity, dict):
        identity["current_year"] = new_year
        identity["current_sem"] = new_sem
        identity["current_sec"] = new_sec
        identity["current_lab_group"] = new_lab
    else:
        setattr(identity, "current_year", new_year)
        setattr(identity, "current_sem", new_sem)
        setattr(identity, "current_sec", new_sec)
        setattr(identity, "current_lab_group", new_lab)

    return {
        "status": "updated",
        "cohort": {"year": new_year, "sem": new_sem, "sec": new_sec},
        "message": f"Successfully updated your cohort to Year {new_year}, Semester {new_sem}, Section {new_sec}.",
        "timetable": get_effective_timetable(identity),
    }