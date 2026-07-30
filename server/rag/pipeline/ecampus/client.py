# High-level client used by tool handlers — replaces the OAuth-based
# ECampusClient from AURA_Agentic_ECampus_Tools.md. Same external shape
# result = client.get_result()

from typing import Optional
from . import pages, parsers, cache, credentials_vault, timetable, timetable_pool, faculty_schedule
from .session import ECampusSession


class ECampusClient:
    def __init__(self, erp_id: str):
        self.erp_id = erp_id
        self._session: Optional[ECampusSession] = None

    def _ensure_session(self) -> ECampusSession:
        if self._session is not None:
            return self._session
        username, password = credentials_vault.get_credentials(self.erp_id)
        session = ECampusSession()
        session.login(username, password)
        self._session = session
        return session

    def _get_cached_or_fetch(self, page_path: str, parse_fn):
        key = cache.cache_key(self.erp_id, page_path)
        cached = cache.get(key)
        if cached is not None:
            return cached
        session = self._ensure_session()
        html = session.get_page(page_path)
        parsed = parse_fn(html)
        cache.set(key, parsed)
        return parsed

    # ── One method per tab ───────────────────────────────────────────────
    def get_student_detail(self) -> dict:
        return self._get_cached_or_fetch(pages.Pages.STUDENT_DETAIL, parsers.parse_student_detail)

    def get_registration(self) -> list[dict]:
        return self._get_cached_or_fetch(pages.Pages.REGISTRATION, parsers.parse_registration)

    def get_course_adjustments(self) -> list[dict]:
        return self._get_cached_or_fetch(pages.Pages.COURSE_ADJUSTMENTS, parsers.parse_course_adjustments)

    def get_result(self) -> dict:
        return self._get_cached_or_fetch(pages.Pages.RESULT, parsers.parse_result)

    def get_cgpa(self) -> dict:
        # Derived from the Result page rather than scraped separately —
        # there's no indication eCampus exposes CGPA on its own page.
        result = self.get_result()
        return {
            "cgpa_raw_label": result.get("cgpa_raw_label"),
            "sgpa_raw_label": result.get("sgpa_raw_label"),
            # TODO: once parse_result's TODOs are filled in with real
            # selectors, this should return clean numeric values instead of
            # raw label text.
        }

    def get_hostel(self) -> dict:
        return self._get_cached_or_fetch(pages.Pages.HOSTEL, parsers.parse_hostel)

    def get_fees(self) -> dict:
        return self._get_cached_or_fetch(pages.Pages.FEES, parsers.parse_fees)

    def get_attendance(self) -> list[dict]:
        return self._get_cached_or_fetch(pages.Pages.ATTENDANCE, parsers.parse_attendance)

    def get_utilities(self) -> dict:
        return self._get_cached_or_fetch(pages.Pages.UTILITIES, parsers.parse_utilities)

    def get_timetable(self) -> list[dict]:
        key = cache.cache_key(self.erp_id, pages.Pages.TIMETABLE)
        cached = cache.get(key)
        if cached is not None:
            entries = cached
        else:
            session = self._ensure_session()
            html = session.get_page(pages.Pages.TIMETABLE)
            entries = timetable.parse_timetable(html)
            cache.set(key, entries)
            # Feed the shared pool so faculty schedules can be derived later —
            # this is the "if I give you a timetable you generate faculty
            # schedule from that only" mechanism from the brief.
            timetable_pool.append_entries(entries)

        return [e.__dict__ for e in entries]

    def close(self) -> None:
        if self._session:
            self._session.logout()
            self._session = None

    # Fix #11: context-manager support so callers can write:
    #   with ECampusClient(erp_id=erp_id) as client:
    #       ...
    # This guarantees close() (and therefore logout()) is always called,
    # even if an exception occurs during the session, preventing dangling
    # authenticated sessions on the eCampus server.
    def __enter__(self) -> "ECampusClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def get_faculty_schedule(faculty_name: str) -> dict:
    # Module-level, not tied to a student's session — pulls from the pool
    # accumulated across every student's get_timetable() call so far. No
    # eCampus login as faculty required for this in phase 1.
    entries = timetable_pool.load_all_entries()
    return faculty_schedule.build_faculty_schedule(entries, faculty_name)
