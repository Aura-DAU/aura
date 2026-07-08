"""
B5 — ERP Connector Service.

Provides named, parameterized read-only methods for every piece of personal
data AURA needs. The LLM and user query text NEVER touch this layer —
only the AccessControlGate (B7) calls it, with typed, pre-validated
arguments.

Two transport modes, auto-selected:
  SQL mode   — if ERP_DB_HOST is set: direct psycopg2 connection to
               the ERP's PostgreSQL database via the aura_readonly service
               account. sslmode=require, default_transaction_read_only=on.
               Use this mode when ERP team grants DB read access.
  Scrape mode — if ERP_DB_HOST is NOT set: falls back to the eCampus
               session-scraper (pipeline/ecampus/client.py). Results are
               mapped to the same return shapes as SQL mode so the rest of
               the system is unaware of the difference.

Security contract (applies to BOTH modes):
  - No method ever accepts a raw SQL string or interpolates user input.
  - Every SQL query uses %s parameterized placeholders.
  - The aura_readonly DB user has SELECT-only grants on specific columns
    (see 03_database_schema.md for the GRANT statements).
  - Connection-level read_only=on means even a bug can't write.
"""

import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from typing import Optional


# ── SQL mode setup ────────────────────────────────────────────────────────

_sql_pool: psycopg2.pool.ThreadedConnectionPool | None = None


def _get_sql_pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _sql_pool
    if _sql_pool is None:
        _sql_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2, maxconn=10,
            host=os.environ["ERP_DB_HOST"],
            port=os.environ.get("ERP_DB_PORT", "5432"),
            dbname=os.environ["ERP_DB_NAME"],
            user=os.environ.get("ERP_DB_USER", "aura_readonly"),
            password=os.environ["ERP_DB_PASS"],
            sslmode="require",
            options="-c default_transaction_read_only=on",
        )
    return _sql_pool


class ERPConnector:
    """
    Public interface — all callers use this class regardless of transport mode.
    """

    def __init__(self):
        self._mode = "sql" if os.environ.get("ERP_DB_HOST") else "scrape"

    # ── Internal SQL helper ───────────────────────────────────────────────

    def _q(self, sql: str, params: tuple) -> list[dict]:
        """
        Executes a parameterized SELECT. Raises an error if sql is not a
        SELECT statement — belt-and-suspenders guard against accidental writes.
        The connection is already read-only at the DB level, but we add a
        code-level check here too.
        (B5 acceptance test: _q("DROP TABLE students", ()) must raise.)
        """
        if not sql.strip().upper().startswith("SELECT"):
            raise ValueError(
                "ERPConnector._q only accepts SELECT statements. "
                f"Received: {sql[:40]!r}"
            )
        p = _get_sql_pool()
        conn = p.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]
        finally:
            p.putconn(conn)

    # ── Scrape-mode helpers ───────────────────────────────────────────────

    def _scrape_client(self, erp_id: str):
        from pipeline.ecampus.client import ECampusClient
        return ECampusClient(erp_id=erp_id)

    # ── Student identity ──────────────────────────────────────────────────

    def get_student_profile(self, roll_number: str) -> Optional[dict]:
        if self._mode == "sql":
            rows = self._q(
                """SELECT roll_number, full_name, dept, program,
                          batch_year, current_semester, enrollment_status
                   FROM students
                   WHERE roll_number = %s AND enrollment_status = 'active'""",
                (roll_number,),
            )
            return rows[0] if rows else None
        # Scrape mode
        client = self._scrape_client(roll_number)
        raw = client.get_student_detail()
        return raw or None

    # ── Academic performance ──────────────────────────────────────────────

    def get_cgpa(self, roll_number: str) -> Optional[dict]:
        if self._mode == "sql":
            rows = self._q(
                """SELECT roll_number, cpi AS cgpa, MAX(semester) AS as_of_semester
                   FROM academic_record
                   WHERE roll_number = %s
                   GROUP BY roll_number, cpi
                   ORDER BY as_of_semester DESC LIMIT 1""",
                (roll_number,),
            )
            return rows[0] if rows else None
        client = self._scrape_client(roll_number)
        return client.get_cgpa()

    def get_semester_performance(self, roll_number: str, semester: Optional[int] = None) -> list[dict]:
        if self._mode == "sql":
            if semester:
                return self._q(
                    "SELECT semester, spi, cpi FROM academic_record WHERE roll_number=%s AND semester=%s ORDER BY semester",
                    (roll_number, semester),
                )
            return self._q(
                "SELECT semester, spi, cpi FROM academic_record WHERE roll_number=%s ORDER BY semester",
                (roll_number,),
            )
        client = self._scrape_client(roll_number)
        result = client.get_result()
        return result.get("grades", [])

    def get_grades(self, roll_number: str, semester: Optional[int] = None,
                   course_code: Optional[str] = None) -> list[dict]:
        if self._mode == "sql":
            if semester and course_code:
                return self._q(
                    "SELECT course_code, course_name, semester, grade, grade_points FROM course_grades WHERE roll_number=%s AND semester=%s AND course_code=%s",
                    (roll_number, semester, course_code),
                )
            if semester:
                return self._q(
                    "SELECT course_code, course_name, semester, grade, grade_points FROM course_grades WHERE roll_number=%s AND semester=%s ORDER BY course_code",
                    (roll_number, semester),
                )
            return self._q(
                "SELECT course_code, course_name, semester, grade, grade_points FROM course_grades WHERE roll_number=%s ORDER BY semester, course_code",
                (roll_number,),
            )
        client = self._scrape_client(roll_number)
        result = client.get_result()
        grades = result.get("grades", [])
        if course_code:
            grades = [g for g in grades if g.get("course_code") == course_code]
        return grades

    # ── Attendance ────────────────────────────────────────────────────────

    def get_attendance(self, roll_number: str, semester: Optional[int] = None,
                       course_code: Optional[str] = None) -> list[dict]:
        if self._mode == "sql":
            if course_code:
                return self._q(
                    """SELECT course_code, semester, total_classes,
                              attended_classes, attendance_pct
                       FROM attendance
                       WHERE roll_number=%s AND course_code=%s AND (%s IS NULL OR semester=%s)""",
                    (roll_number, course_code, semester, semester),
                )
            return self._q(
                """SELECT course_code, semester, total_classes,
                          attended_classes, attendance_pct
                   FROM attendance
                   WHERE roll_number=%s AND (%s IS NULL OR semester=%s)
                   ORDER BY semester, course_code""",
                (roll_number, semester, semester),
            )
        client = self._scrape_client(roll_number)
        rows = client.get_attendance()
        if course_code:
            rows = [r for r in rows if r.get("course_code") == course_code]
        return rows

    # ── Faculty / advisor relationship checks ─────────────────────────────

    def is_advisee(self, faculty_erp_id: str, student_roll: str) -> bool:
        if self._mode == "sql":
            rows = self._q(
                """SELECT 1 FROM advisee_mapping
                   WHERE advisor_employee_id=%s AND student_roll_number=%s
                     AND (end_date IS NULL OR end_date > NOW()) LIMIT 1""",
                (faculty_erp_id, student_roll),
            )
            return bool(rows)
        # Scrape mode: not implementable without faculty credentials — deny
        return False

    def get_shared_courses(self, faculty_erp_id: str, student_roll: str) -> list[str]:
        if self._mode == "sql":
            rows = self._q(
                """SELECT ca.course_code
                   FROM course_assignments ca
                   JOIN enrollments e ON ca.course_code=e.course_code AND ca.semester=e.semester
                   WHERE ca.employee_id=%s AND e.roll_number=%s""",
                (faculty_erp_id, student_roll),
            )
            return [r["course_code"] for r in rows]
        return []

    def student_in_batch(self, student_roll: str, dept: str, batch_year: str) -> bool:
        if self._mode == "sql":
            rows = self._q(
                """SELECT 1 FROM students
                   WHERE roll_number=%s AND dept=%s AND batch_year=%s
                     AND enrollment_status='active' LIMIT 1""",
                (student_roll, dept, batch_year),
            )
            return bool(rows)
        return False

    def get_faculty_courses(self, faculty_erp_id: str, semester: Optional[int] = None) -> list[dict]:
        if self._mode == "sql":
            return self._q(
                """SELECT course_code, semester, batch FROM course_assignments
                   WHERE employee_id=%s AND (%s IS NULL OR semester=%s)
                   ORDER BY semester DESC""",
                (faculty_erp_id, semester, semester),
            )
        return []

    def get_advisees(self, faculty_erp_id: str) -> list[dict]:
        if self._mode == "sql":
            return self._q(
                """SELECT am.student_roll_number, s.full_name, s.dept, s.current_semester
                   FROM advisee_mapping am
                   JOIN students s ON s.roll_number=am.student_roll_number
                   WHERE am.advisor_employee_id=%s
                     AND (am.end_date IS NULL OR am.end_date > NOW())
                     AND s.enrollment_status='active'
                   ORDER BY s.full_name""",
                (faculty_erp_id,),
            )
        return []

    def find_student_by_name(self, name: str) -> Optional[dict]:
        """Fuzzy name lookup — only available in SQL mode."""
        if self._mode == "sql":
            rows = self._q(
                "SELECT roll_number, full_name FROM students WHERE full_name ILIKE %s AND enrollment_status='active' LIMIT 1",
                (f"%{name}%",),
            )
            return rows[0] if rows else None
        return None

    # ── Aggregate queries (anonymized — no individual records returned) ───

    def get_class_aggregate(self, course_code: str, semester: Optional[int] = None) -> dict:
        """
        Returns anonymized class-level statistics for a course.
        NEVER returns individual student records — only averages/counts.
        Called only after the AccessControlGate confirms the requesting
        faculty member teaches this course.
        """
        if self._mode == "sql":
            cgpa_rows = self._q(
                """SELECT AVG(cg.grade_points) AS avg_grade_points,
                          COUNT(DISTINCT e.roll_number) AS student_count
                   FROM course_grades cg
                   JOIN enrollments e ON e.roll_number = cg.roll_number
                                      AND e.course_code = cg.course_code
                   WHERE cg.course_code = %s
                     AND (%s IS NULL OR cg.semester = %s)""",
                (course_code, semester, semester),
            )
            att_rows = self._q(
                """SELECT AVG(attendance_pct) AS avg_attendance_pct,
                          COUNT(DISTINCT roll_number) AS student_count
                   FROM attendance
                   WHERE course_code = %s
                     AND (%s IS NULL OR semester = %s)""",
                (course_code, semester, semester),
            )
            return {
                "course_code":         course_code,
                "grades_aggregate":    cgpa_rows[0] if cgpa_rows else {},
                "attendance_aggregate": att_rows[0] if att_rows else {},
                "note": "Anonymized aggregate — no individual student data included.",
            }
        # Scrape mode: not implementable without individual student data
        return {
            "course_code": course_code,
            "note": "Aggregate data unavailable in scrape mode — requires direct ERP DB access.",
        }

    # ── B2-AUTH-5: Program Coordinator level methods ──────────────────────

    def student_in_program(self, student_erp_id: str, program_id: str) -> bool:
        """Check if a student belongs to a specific program (e.g. 'BTech-ICT').
        Used by AccessControlGate for faculty_coord binding checks."""
        if self._mode == "sql":
            rows = self._q(
                """SELECT 1 FROM students
                   WHERE roll_number = %s
                     AND program = %s
                     AND enrollment_status = 'active'
                   LIMIT 1""",
                (student_erp_id, program_id),
            )
            return bool(rows)
        # Scrape mode: not deterministic without program data — deny safely
        return False

    def get_program_students(
        self,
        program_id: str,
        batch_year: Optional[int] = None,
        enrollment_status: str = "active",
    ) -> list[dict]:
        """All students enrolled in a given program. Coordinator-scoped."""
        if self._mode == "sql":
            if batch_year:
                return self._q(
                    """SELECT roll_number, full_name, dept, current_semester,
                              enrollment_status, batch_year
                       FROM students
                       WHERE program = %s
                         AND batch_year = %s
                         AND enrollment_status = %s
                       ORDER BY roll_number""",
                    (program_id, batch_year, enrollment_status),
                )
            return self._q(
                """SELECT roll_number, full_name, dept, current_semester,
                          enrollment_status, batch_year
                   FROM students
                   WHERE program = %s
                     AND enrollment_status = %s
                   ORDER BY batch_year DESC, roll_number""",
                (program_id, enrollment_status),
            )
        return []

    def get_program_courses(
        self, program_id: str, semester: Optional[int] = None
    ) -> list[dict]:
        """All courses in a program for a given semester (or current)."""
        if self._mode == "sql":
            if semester:
                return self._q(
                    """SELECT pc.course_code, pc.course_name, pc.credits,
                              pc.course_type, ca.employee_id AS instructor_id,
                              f.full_name AS instructor_name
                       FROM program_courses pc
                       LEFT JOIN course_assignments ca
                              ON ca.course_code = pc.course_code
                             AND ca.semester = %s
                       LEFT JOIN faculty f ON f.employee_id = ca.employee_id
                       WHERE pc.program = %s
                       ORDER BY pc.course_type, pc.course_code""",
                    (semester, program_id),
                )
            return self._q(
                """SELECT course_code, course_name, credits, course_type
                   FROM program_courses
                   WHERE program = %s
                   ORDER BY course_type, course_code""",
                (program_id,),
            )
        return []

    def get_program_grade_distribution(
        self, program_id: str, course_code: str, semester: Optional[int] = None
    ) -> dict:
        """Aggregate grade histogram for a course within a program.
        Returns anonymized counts — no individual student data."""
        if self._mode == "sql":
            rows = self._q(
                """SELECT cg.grade, COUNT(*) AS count
                   FROM course_grades cg
                   JOIN students s ON s.roll_number = cg.roll_number
                   WHERE s.program = %s
                     AND cg.course_code = %s
                     AND (%s IS NULL OR cg.semester = %s)
                   GROUP BY cg.grade
                   ORDER BY cg.grade""",
                (program_id, course_code, semester, semester),
            )
            return {
                "program": program_id,
                "course_code": course_code,
                "distribution": {r["grade"]: r["count"] for r in rows},
                "note": "Anonymized aggregate — no individual records.",
            }
        return {"note": "SQL mode required for grade distribution."}

    def get_program_academic_standing(self, program_id: str) -> list[dict]:
        """Students in a program with probation/backlog flags. Coordinator use."""
        if self._mode == "sql":
            return self._q(
                """SELECT s.roll_number, s.full_name, s.current_semester,
                          ar.cpi,
                          COUNT(cg.course_code) FILTER (
                              WHERE cg.grade IN ('F', 'I', 'W')
                          ) AS backlog_count
                   FROM students s
                   LEFT JOIN academic_record ar
                          ON ar.roll_number = s.roll_number
                         AND ar.semester = s.current_semester
                   LEFT JOIN course_grades cg ON cg.roll_number = s.roll_number
                   WHERE s.program = %s AND s.enrollment_status = 'active'
                   GROUP BY s.roll_number, s.full_name, s.current_semester, ar.cpi
                   ORDER BY ar.cpi ASC NULLS LAST""",
                (program_id,),
            )
        return []

    def get_program_elective_demand(
        self, program_id: str, semester: int
    ) -> list[dict]:
        """Elective demand vs capacity for a program's upcoming semester."""
        if self._mode == "sql":
            return self._q(
                """SELECT pc.course_code, pc.course_name,
                          pc.seat_capacity,
                          COUNT(e.roll_number) AS enrolled,
                          COUNT(wl.roll_number) AS waitlisted
                   FROM program_courses pc
                   LEFT JOIN enrollments e
                          ON e.course_code = pc.course_code
                         AND e.semester = %s
                   LEFT JOIN waitlist wl
                          ON wl.course_code = pc.course_code
                         AND wl.semester = %s
                   WHERE pc.program = %s
                     AND pc.course_type = 'elective'
                   GROUP BY pc.course_code, pc.course_name, pc.seat_capacity
                   ORDER BY pc.course_code""",
                (semester, semester, program_id),
            )
        return []

    # ── B2-AUTH-6: Dean level methods ─────────────────────────────────────

    def get_all_students(
        self,
        enrollment_status: str = "active",
        dept: Optional[str] = None,
    ) -> list[dict]:
        """Full student list across all programs. Dean/admin scope only.
        Never call this from a student or general-faculty code path."""
        if self._mode == "sql":
            if dept:
                return self._q(
                    """SELECT roll_number, full_name, dept, program,
                              batch_year, current_semester, enrollment_status
                       FROM students
                       WHERE enrollment_status = %s AND dept = %s
                       ORDER BY program, batch_year, roll_number""",
                    (enrollment_status, dept),
                )
            return self._q(
                """SELECT roll_number, full_name, dept, program,
                          batch_year, current_semester, enrollment_status
                   FROM students
                   WHERE enrollment_status = %s
                   ORDER BY program, batch_year, roll_number""",
                (enrollment_status,),
            )
        return []

    def get_hostel_master(self) -> list[dict]:
        """Full hostel occupancy map. Dean of Students scope only."""
        if self._mode == "sql":
            return self._q(
                """SELECT ha.room_number, ha.block, ha.floor,
                          ha.student_roll, s.full_name, s.program,
                          ha.mess_group, ha.allotment_date
                   FROM hostel_allotments ha
                   JOIN students s ON s.roll_number = ha.student_roll
                   WHERE ha.active = TRUE
                   ORDER BY ha.block, ha.floor, ha.room_number""",
                (),
            )
        return []

    def get_disciplinary_cases(
        self,
        status: Optional[str] = None,
        student_erp_id: Optional[str] = None,
    ) -> list[dict]:
        """Disciplinary committee cases. Dean of Students + admin scope only.
        Never surfaces individual case details unless explicitly requested
        by an authorized dean — the gate checks this before calling."""
        if self._mode == "sql":
            return self._q(
                """SELECT dc.case_id, dc.student_roll, s.full_name,
                           dc.incident_date, dc.category, dc.status,
                           dc.committee_decision
                    FROM disciplinary_cases dc
                    JOIN students s ON s.roll_number = dc.student_roll
                    WHERE (%s IS NULL OR dc.status = %s)
                      AND (%s IS NULL OR dc.student_roll = %s)
                    ORDER BY dc.incident_date DESC""",
                (status, status, student_erp_id, student_erp_id),
            )
        return []

    def get_all_grievances(
        self,
        grievance_type: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[dict]:
        """All student grievances. Dean of Students scope only."""
        if self._mode == "sql":
            return self._q(
                """SELECT g.grievance_id, g.student_roll, g.grievance_type,
                          g.submitted_at, g.status, g.assigned_to,
                          g.resolution_summary
                   FROM grievances g
                   WHERE (%s IS NULL OR g.grievance_type = %s)
                     AND (%s IS NULL OR g.status = %s)
                   ORDER BY g.submitted_at DESC""",
                (grievance_type, grievance_type, status, status),
            )
        return []

    def get_scholarship_records(
        self, student_erp_id: Optional[str] = None
    ) -> list[dict]:
        """Scholarship and aid records. Dean of Students / registrar scope."""
        if self._mode == "sql":
            if student_erp_id:
                return self._q(
                    """SELECT scholarship_name, amount, semester,
                              eligibility_criteria, status
                       FROM scholarships
                       WHERE student_roll = %s
                       ORDER BY semester DESC""",
                    (student_erp_id,),
                )
            return self._q(
                """SELECT s.roll_number, st.full_name, s.scholarship_name,
                          s.amount, s.semester, s.status
                   FROM scholarships s
                   JOIN students st ON st.roll_number = s.student_roll
                   ORDER BY s.semester DESC, st.full_name""",
                (),
            )
        return []

    def get_btp_eligible_students(self, dept: Optional[str] = None) -> list[dict]:
        """Students who have completed the minimum credits for BTP.
        Faculty (general) read-only — filtered by dept if given."""
        if self._mode == "sql":
            return self._q(
                """SELECT s.roll_number, s.full_name, s.dept, s.current_semester,
                          ar.cpi
                   FROM students s
                   JOIN academic_record ar ON ar.roll_number = s.roll_number
                     AND ar.semester = s.current_semester
                   WHERE s.enrollment_status = 'active'
                     AND s.current_semester >= 6
                     AND ar.cpi >= 6.0
                     AND (%s IS NULL OR s.dept = %s)
                     AND NOT EXISTS (
                         SELECT 1 FROM btp_registrations b
                         WHERE b.student_roll = s.roll_number
                           AND b.status = 'active'
                     )
                   ORDER BY ar.cpi DESC""",
                (dept, dept),
            )
        return []

    def get_exploration_mentees(self, faculty_erp_id: str) -> list[dict]:
        """Students in Exploration Project under this faculty's mentorship."""
        if self._mode == "sql":
            return self._q(
                """SELECT ep.student_roll, s.full_name, s.dept,
                          s.current_semester, ep.project_title,
                          ep.status, ep.grade
                   FROM exploration_projects ep
                   JOIN students s ON s.roll_number = ep.student_roll
                   WHERE ep.mentor_faculty_id = %s
                     AND ep.status IN ('active', 'submitted')
                   ORDER BY s.full_name""",
                (faculty_erp_id,),
            )
        return []

    def get_btp_students(self, faculty_erp_id: str) -> list[dict]:
        """Students currently doing BTP under this faculty."""
        if self._mode == "sql":
            return self._q(
                """SELECT b.student_roll, s.full_name, s.dept,
                          s.current_semester, b.title, b.status,
                          b.co_guide_id
                   FROM btp_registrations b
                   JOIN students s ON s.roll_number = b.student_roll
                   WHERE b.guide_faculty_id = %s
                     AND b.status = 'active'
                   ORDER BY s.full_name""",
                (faculty_erp_id,),
            )
        return []

    def get_faculty_teaching_schedule(self, faculty_erp_id: str) -> list[dict]:
        """Full teaching schedule for a faculty member (own profile use)."""
        if self._mode == "sql":
            return self._q(
                """SELECT ca.course_code, pc.course_name, ca.semester,
                          ca.batch, ts.day, ts.start_time,
                          ts.end_time, ts.room
                   FROM course_assignments ca
                   JOIN program_courses pc ON pc.course_code = ca.course_code
                   LEFT JOIN timetable_slots ts ON ts.course_code = ca.course_code
                     AND ts.semester = ca.semester
                   WHERE ca.employee_id = %s
                   ORDER BY ts.day, ts.start_time""",
                (faculty_erp_id,),
            )
        # Scrape mode: use pooled timetable data
        from pipeline.ecampus.timetable_pool import load_all_entries
        from pipeline.ecampus.faculty_schedule import build_faculty_schedule
        entries = load_all_entries()
        return [build_faculty_schedule(entries, faculty_erp_id)]