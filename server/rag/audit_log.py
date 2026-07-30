# Audit Log — PostgreSQL append-only, never crashes the request (B2-AUTH-9).
# scope_context field (added in 002_extend_roles.sql) records coordinator
# "coordinator:BTech-ICT" or "UG convenor → BTech-ICT".

import logging
import traceback
from typing import Optional

logger = logging.getLogger(__name__)


class AuditLog:

    def __init__(self, db_module=None):
        if db_module is None:
            import db.connection as db_module  # noqa: PLC0415
        self._db = db_module

    def record(
        self,
        erp_id:         str,
        role:           str,
        query_text:     str,
        query_type:     str,
        access_granted: bool,
        target_erp_id:  Optional[str]       = None,
        denial_reason:  Optional[str]       = None,
        erp_tables:     Optional[list[str]] = None,
        scope_context:  Optional[str]       = None,   # B2-AUTH-9: coordinator/dean scope
    ) -> None:
        # Insert one audit row. Never raises — wraps in try/except.
        # scope_context captures fine-grained scope info such as
        # 'coordinator:BTech-ICT' or 'dean_students' for administrative roles.
        try:
            self._db.execute(
                """INSERT INTO audit_log
                   (erp_id, role, query_text, query_type,
                    target_erp_id, access_granted, denial_reason,
                    erp_tables, scope_context)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    erp_id,
                    role,
                    query_text,
                    query_type,
                    target_erp_id,
                    access_granted,
                    denial_reason,
                    erp_tables or [],
                    scope_context,
                ),
            )
        except Exception:
            logger.error(
                "audit_log INSERT failed — continuing.\n%s",
                traceback.format_exc(),
            )