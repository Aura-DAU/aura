"""Immutable, request-scoped identity and academic context."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from api.auth import Identity


PROFILE_STALE_AFTER = timedelta(hours=24)
ENROLLMENT_STALE_AFTER = timedelta(hours=6)

_SCOPE_REFRESH_LOCK = Lock()
_SCOPE_REFRESH_QUEUE: set[str] = set()
_SCOPE_REFRESH_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="academic-scope-refresh")
logger = logging.getLogger(__name__)

_SCOPE_LOOKUP_SQL = """
SELECT si.identity_version, si.admission_year, si.programme_id,
       si.branch_id, si.department_id, si.degree_level,
       sap.profile_version, sap.academic_status,
       sap.expected_graduation_year, sap.curriculum_version,
       sap.regulation_version, sap.synced_at,
       ses.id AS enrollment_snapshot_id, ses.current_semester,
       ses.captured_at AS enrollment_captured_at
  FROM student_identity si
  JOIN student_academic_profile sap ON sap.erp_id = si.erp_id
  LEFT JOIN student_enrollment_snapshot ses
    ON ses.erp_id = si.erp_id AND ses.is_current = TRUE
 WHERE si.erp_id = %s
"""


@dataclass(frozen=True)
class AcademicScope:
    erp_id: str
    identity_version: int
    admission_year: int
    programme_id: str
    branch_id: Optional[str]
    department_id: Optional[str]
    degree_level: str
    profile_version: int
    academic_status: str
    expected_graduation_year: Optional[int]
    curriculum_version: Optional[str]
    regulation_version: Optional[str]
    enrollment_snapshot_id: Optional[str]
    current_semester: Optional[int]
    registered_course_codes: tuple[str, ...]
    elective_course_codes: tuple[str, ...]
    profile_stale: bool
    enrollment_stale: bool

    def document_is_eligible(self, metadata: dict) -> bool:
        """Defence-in-depth applicability check after retrieval."""
        scope = metadata.get("applicability_scope")
        if scope == "global":
            return True
        if scope not in {"programme", "curriculum", "course"}:
            return False
        if metadata.get("programme_id") != self.programme_id:
            return False
        degree_level = metadata.get("degree_level")
        if degree_level and degree_level != self.degree_level:
            return False
        branch_id = metadata.get("branch_id")
        if branch_id and branch_id != self.branch_id:
            return False
        start = metadata.get("admission_year_from")
        end = metadata.get("admission_year_to")
        if not isinstance(start, int) or not isinstance(end, int):
            return False
        if not start <= self.admission_year <= end:
            return False
        if scope == "course":
            course_code = metadata.get("course_code")
            if course_code and course_code not in self.registered_course_codes:
                return False
        return True


@dataclass(frozen=True)
class RequestContext:
    identity: Identity
    effective_role: str
    academic_scope: Optional[AcademicScope]
    tracking_flags: dict = field(default_factory=dict)


def _sync_scope_snapshot(erp_id: str) -> None:
    """Best-effort background synchronization hook for stale scope reads."""
    try:
        import db.connection as db_conn

        db_conn.execute(
            """
            INSERT INTO student_academic_profile (erp_id, profile_version, synced_at, academic_status)
            VALUES (%s, 1, NOW(), 'active')
            ON CONFLICT (erp_id) DO UPDATE SET
               profile_version = COALESCE(student_academic_profile.profile_version, 0) + 1,
               synced_at = NOW(),
               academic_status = COALESCE(student_academic_profile.academic_status, 'active')
            """,
            (erp_id,),
        )
        db_conn.execute(
            """
            INSERT INTO student_enrollment_snapshot (erp_id, is_current, current_semester, captured_at)
            VALUES (%s, TRUE, NULL, NOW())
            ON CONFLICT (erp_id, is_current) DO UPDATE SET
               captured_at = NOW()
            """,
            (erp_id,),
        )
    except Exception as exc:
        # Background refresh is best-effort; failures must not break the request.
        logger.warning("Academic scope background refresh failed for %s: %s", erp_id, exc)
        return


def _enqueue_scope_refresh(erp_id: str) -> None:
    if not erp_id:
        return
    with _SCOPE_REFRESH_LOCK:
        if erp_id in _SCOPE_REFRESH_QUEUE:
            return
        _SCOPE_REFRESH_QUEUE.add(erp_id)

    def _run() -> None:
        try:
            _sync_scope_snapshot(erp_id)
        finally:
            with _SCOPE_REFRESH_LOCK:
               _SCOPE_REFRESH_QUEUE.discard(erp_id)

    _SCOPE_REFRESH_EXECUTOR.submit(_run)


class AcademicScopeResolver:
    """Resolves the canonical student context once for a request."""

    def resolve(self, identity: Identity, effective_role: str) -> RequestContext:
        try:
            from pipeline.personal_data.tracking_store import get_tracking_flags
            tracking_flags = get_tracking_flags(identity.erp_id)
        except Exception as exc:
            logger.warning("Failed to fetch tracking flags for %s: %s", identity.erp_id, exc)
            tracking_flags = {}

        if identity.role != "student":
            return RequestContext(identity=identity, effective_role=effective_role, academic_scope=None, tracking_flags=tracking_flags)

        try:
            import db.connection as db_conn

            rows = db_conn.query(_SCOPE_LOOKUP_SQL, (identity.erp_id,))
            if not rows:
                # Backfill for students who logged in before academic-scope
                # persistence shipped, or whose resolve write failed.
                try:
                    from api.academic_scope_persist import ensure_student_academic_scope

                    if ensure_student_academic_scope(identity):
                        rows = db_conn.query(_SCOPE_LOOKUP_SQL, (identity.erp_id,))
                except Exception as backfill_exc:
                    logger.warning(
                        "Academic scope backfill failed for %s: %s",
                        identity.erp_id,
                        backfill_exc,
                    )
                if not rows:
                    return RequestContext(
                        identity=identity,
                        effective_role=effective_role,
                        academic_scope=None,
                        tracking_flags=tracking_flags,
                    )

            row = rows[0]
            courses: list[dict] = []
            snapshot_id = row.get("enrollment_snapshot_id")
            if snapshot_id:
               courses = db_conn.query(
                  "SELECT course_code, enrollment_type FROM student_course_enrollment WHERE snapshot_id = %s",
                  (snapshot_id,),
               )
            now = datetime.now(timezone.utc)
            profile_synced = row.get("synced_at")
            enrollment_captured = row.get("enrollment_captured_at")
            profile_stale = not profile_synced or now - profile_synced > PROFILE_STALE_AFTER
            enrollment_stale = bool(snapshot_id) and (
               not enrollment_captured or now - enrollment_captured > ENROLLMENT_STALE_AFTER
            )
            registered = tuple(course.get("course_code") for course in courses if course.get("course_code"))
            electives = tuple(
               course.get("course_code") for course in courses
               if course.get("course_code") and course.get("enrollment_type") == "elective"
            )
            scope = AcademicScope(
               erp_id=identity.erp_id,
               identity_version=row["identity_version"],
               admission_year=row["admission_year"],
               programme_id=row["programme_id"],
               branch_id=row.get("branch_id"),
               department_id=row.get("department_id"),
               degree_level=row["degree_level"],
               profile_version=row["profile_version"],
               academic_status=row["academic_status"],
               expected_graduation_year=row.get("expected_graduation_year"),
               curriculum_version=row.get("curriculum_version"),
               regulation_version=row.get("regulation_version"),
               enrollment_snapshot_id=str(snapshot_id) if snapshot_id else None,
               current_semester=row.get("current_semester"),
               registered_course_codes=registered,
               elective_course_codes=electives,
               profile_stale=profile_stale,
               enrollment_stale=enrollment_stale,
            )
            if profile_stale or enrollment_stale:
               _enqueue_scope_refresh(identity.erp_id)
            return RequestContext(identity=identity, effective_role=effective_role, academic_scope=scope, tracking_flags=tracking_flags)
        except Exception as exc:
            logger.warning("Academic scope resolution failed for %s: %s", identity.erp_id, exc)
            return RequestContext(identity=identity, effective_role=effective_role, academic_scope=None, tracking_flags=tracking_flags)
