"""
Audit Log — PostgreSQL, append-only, never crashes the request.

Updated for SSO architecture: removed the separate `user_id` UUID parameter
since the users table no longer exists. `erp_id` is the sole requester
identifier, matching the audit_log table schema in 001_auth_schema.sql.
"""

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
    ) -> None:
        """
        Insert one audit row. Never raises — if the DB write fails, logs
        the error to stderr but does NOT propagate (the chat response returns).
        """
        try:
            self._db.execute(
                """INSERT INTO audit_log
                   (erp_id, role, query_text, query_type,
                    target_erp_id, access_granted, denial_reason, erp_tables)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    erp_id,
                    role,
                    query_text,
                    query_type,
                    target_erp_id,
                    access_granted,
                    denial_reason,
                    erp_tables or [],
                ),
            )
        except Exception:
            logger.error(
                "audit_log INSERT failed — continuing without audit row.\n%s",
                traceback.format_exc(),
            )
