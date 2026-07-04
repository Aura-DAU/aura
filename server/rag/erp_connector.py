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


_USE_SQL = bool(os.environ.get("ERP_DB_HOST"))


class ERPConnector:
    """
    Public interface — all callers use this class regardless of transport mode.
    """

    def __init__(self):
        self._mode = "sql" if _USE_SQL else "scrape"

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
