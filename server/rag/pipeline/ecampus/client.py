"""
High-level client used by tool handlers.

Key insight from real HTML (July 2026):
  - Registration and grades both require a TWO-STEP fetch:
      1. GET the list page → get semester list + (stdid, semesterID) per semester
      2. POST to the edit/detail servlet with stdid + SemesterID → get actual data
  - Grade card POST: stdid=12436, SemesterID=1455 → Semester IV
  - Registration POST: same pattern via StudentRegistrationEditServlet

  The client handles both steps transparently — callers just call
  get_registration() or get_grades() and get structured data back.
"""

from . import pages, parsers, cache, credentials_vault, timetable, timetable_pool, faculty_schedule
from .session import ECampusSession


class ECampusClient:
    def __init__(self, erp_id: str):
        self.erp_id = erp_id
        self._session: ECampusSession | None = None
        self._std_id: str | None = None   # internal DB id (e.g. "12436"), different from ERP ID
        self._is_mock = erp_id.startswith("DEMO")

    def _ensure_session(self) -> ECampusSession:
        if self._is_mock:
            return None
        if self._session is not None:
            return self._session
        username, password = credentials_vault.get_credentials(self.erp_id)
        session = ECampusSession()
        session.login(username, password)
        self._session = session
        return session


    def _get(self, path: str) -> str:
        return self._ensure_session().get_page(path)

    def _post_form(self, path: str, data: dict) -> str:
        """POST a form to a servlet path with given data fields."""
        session = self._ensure_session()
        import requests as _req
        from .session import ECAMPUS_BASE_URL
        resp = session.http.post(ECAMPUS_BASE_URL + path, data=data, timeout=15)
        resp.raise_for_status()
        return resp.text

    def _cached(self, key_suffix: str, fetch_fn):
        key = cache.cache_key(self.erp_id, key_suffix)
        cached = cache.get(key)
        if cached is not None:
            return cached
        result = fetch_fn()
        cache.set(key, result)
        return result

    # ── Student Detail ─────────────────────────────────────────────────────
    def get_student_detail(self) -> dict:
        if self._is_mock:
            return {
                "full_name": "Demo Student",
                "student_id": "202301015",
                "program": "B.Tech ICT",
                "current_semester": "Semester IV (2025-26 Winter)",
                "advisor": "Dr. Amit Bhatt",
            }
        def fetch():
            html = self._get(pages.Pages.STUDENT_DETAIL)
            return parsers.parse_student_detail(html)
        return self._cached("student_detail", fetch)

    # ── Registration ───────────────────────────────────────────────────────
    def get_registration_list(self) -> list[dict]:
        """Returns list of semesters with registration dates."""
        if self._is_mock:
            return [
                {"semester": "Semester I (2024-25 Autumn)", "semester_id": "1", "std_id": "DEMO123", "registered": True},
                {"semester": "Semester II (2024-25 Winter)", "semester_id": "2", "std_id": "DEMO123", "registered": True},
                {"semester": "Semester III (2025-26 Autumn)", "semester_id": "3", "std_id": "DEMO123", "registered": True},
                {"semester": "Semester IV (2025-26 Winter)", "semester_id": "4", "std_id": "DEMO123", "registered": True},
            ]
        def fetch():
            html = self._get(pages.Pages.REGISTRATION_LIST)
            return parsers.parse_registration_list(html)
        return self._cached("registration_list", fetch)

    def get_registration(self, semester: str | None = None) -> dict:
        """
        Returns enrolled courses for a semester (default: latest registered).
        Requires a two-step fetch: list → POST to edit servlet.
        """
        if self._is_mock:
            return {
                "semester": "Semester IV (2025-26 Winter)",
                "courses": [
                    {"course_code": "IT-302", "course_name": "Computer Networks", "credits": "4", "type": "Core"},
                    {"course_code": "IT-304", "course_name": "Software Engineering", "credits": "4", "type": "Core"},
                    {"course_code": "HS-201", "course_name": "Technical Writing", "credits": "3", "type": "Core"},
                ]
            }
        def fetch():
            sem_list = self.get_registration_list()
            # Pick the most recently registered semester (has a reg_date)
            registered = [s for s in sem_list if s.get("registered") and s.get("semester_id")]
            if not registered:
                return {"courses": [], "semester": None}

            if semester:
                target = next((s for s in registered if semester.lower() in s["semester"].lower()), registered[-1])
            else:
                target = registered[-1]  # latest

            html = self._post_form(pages.Pages.REGISTRATION_EDIT, {
                "stdid":      target["std_id"],
                "SemesterID": target["semester_id"],
            })
            return parsers.parse_registration_courses(html)

        return self._cached(f"registration_{semester or 'latest'}", fetch)

    # ── Grades ─────────────────────────────────────────────────────────────
    def get_grade_semester_list(self) -> list[dict]:
        """Returns list of semesters that have grade cards available."""
        if self._is_mock:
            return [
                {"semester": "Semester I (2024-25 Autumn)", "semester_id": "1", "std_id": "DEMO123", "has_grades": True},
                {"semester": "Semester II (2024-25 Winter)", "semester_id": "2", "std_id": "DEMO123", "has_grades": True},
                {"semester": "Semester III (2025-26 Autumn)", "semester_id": "3", "std_id": "DEMO123", "has_grades": True},
                {"semester": "Semester IV (2025-26 Winter)", "semester_id": "4", "std_id": "DEMO123", "has_grades": True},
            ]
        def fetch():
            html = self._get(pages.Pages.GRADE_SEMESTER_LIST)
            return parsers.parse_grade_semester_list(html)
        return self._cached("grade_semester_list", fetch)

    def get_grade_card(self, semester: str | None = None) -> dict:
        """
        Returns grade card for a semester (default: latest with grades).
        Two-step fetch: semester list → POST to GradeCourseListServlet.
        """
        if self._is_mock:
            return {
                "semester": semester or "Semester IV (2025-26 Winter)",
                "spi": "8.50",
                "cpi": "8.75",
                "credits_earned_cum": "80",
                "courses": [
                    {"course_code": "IT-302", "course_name": "Computer Networks", "credits": "4", "grade": "AA"},
                    {"course_code": "IT-304", "course_name": "Software Engineering", "credits": "4", "grade": "AB"},
                    {"course_code": "HS-201", "course_name": "Technical Writing", "credits": "3", "grade": "AA"},
                ]
            }
        def fetch():
            sem_list = self.get_grade_semester_list()
            graded = [s for s in sem_list if s.get("has_grades") and s.get("semester_id")]
            if not graded:
                return {"courses": [], "spi": None, "cpi": None}

            if semester:
                target = next((s for s in graded if semester.lower() in s["semester"].lower()), graded[-1])
            else:
                target = graded[-1]

            html = self._post_form(pages.Pages.GRADE_COURSE_LIST, {
                "stdid":      target["std_id"],
                "SemesterID": target["semester_id"],
            })
            return parsers.parse_grade_card(html)

        return self._cached(f"grade_card_{semester or 'latest'}", fetch)

    def get_result(self) -> dict:
        """Returns latest semester grade card. Alias used by tool_registry."""
        return self.get_grade_card()

    def get_cgpa(self) -> dict:
        """Returns CPI (cumulative) and SPI (latest semester) from grade card."""
        card = self.get_grade_card()
        return {
            "cgpa":           card.get("cpi"),
            "spi":            card.get("spi"),
            "as_of_semester": card.get("semester"),
            "credits_earned": card.get("credits_earned_cum"),
        }

    def get_all_grades(self) -> list[dict]:
        """Fetches grade cards for ALL semesters with results. May be slow first time."""
        if self._is_mock:
            return [
                self.get_grade_card("Semester I (2024-25 Autumn)"),
                self.get_grade_card("Semester II (2024-25 Winter)"),
                self.get_grade_card("Semester III (2025-26 Autumn)"),
                self.get_grade_card("Semester IV (2025-26 Winter)"),
            ]
        def fetch():
            sem_list = self.get_grade_semester_list()
            graded = [s for s in sem_list if s.get("has_grades") and s.get("semester_id")]
            all_cards = []
            for sem in graded:
                html = self._post_form(pages.Pages.GRADE_COURSE_LIST, {
                    "stdid":      sem["std_id"],
                    "SemesterID": sem["semester_id"],
                })
                card = parsers.parse_grade_card(html)
                card["_semester_label"] = sem["semester"]
                all_cards.append(card)
            return all_cards
        return self._cached("all_grades", fetch)

    # ── Timetable ──────────────────────────────────────────────────────────
    def get_timetable(self) -> list[dict]:
        if self._is_mock:
            return [
                {"day": "Monday", "time": "09:00 AM - 10:30 AM", "course": "Computer Networks", "room": "Lab 3, Phase 1"},
                {"day": "Monday", "time": "11:00 AM - 12:30 PM", "course": "Software Engineering", "room": "Room 102"},
                {"day": "Wednesday", "time": "02:00 PM - 03:30 PM", "course": "Technical Writing", "room": "Room 110"},
            ]
        return []

    # ── Attendance ─────────────────────────────────────────────────────────
    def get_attendance(self) -> list[dict]:
        if self._is_mock:
            return [
                {"course": "Computer Networks", "attendance_percentage": "82.5"},
                {"course": "Software Engineering", "attendance_percentage": "71.0"},
                {"course": "Technical Writing", "attendance_percentage": "95.0"},
            ]
        return []

    # ── Hostel ─────────────────────────────────────────────────────────────
    def get_hostel(self) -> dict:
        """Hostel rules/policy page — not personal data, just static rules."""
        if self._is_mock:
            return {"raw_text": "Mock hostel rules: 1. In-time: 10:00 PM. 2. Quiet hours: 11:00 PM - 06:00 AM."}
        def fetch():
            html = self._get(pages.Pages.HOSTEL_RULES)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            return {"raw_text": soup.get_text("\n", strip=True)}
        return self._cached("hostel", fetch)

    # ── Fees ───────────────────────────────────────────────────────────────
    def get_fees(self) -> dict:
        """
        Fee receipts page. Returns structured fee history.
        """
        if self._is_mock:
            return {"raw_text": "Mock receipt: Tuition Fee Semester IV: Paid INR 1,20,000"}
        def fetch():
            html = self._get(pages.Pages.FEE_RECEIPTS_CANDIDATE)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            return {"raw_text": soup.get_text("\n", strip=True)}
        return self._cached("fees", fetch)

    def close(self) -> None:
        if self._session:
            self._session.logout()
            self._session = None

    def __enter__(self) -> "ECampusClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()



def get_faculty_schedule(faculty_name: str) -> dict:
    """Module-level — pulls from pooled timetable data accumulated from students."""
    entries = timetable_pool.load_all_entries()
    return faculty_schedule.build_faculty_schedule(entries, faculty_name)