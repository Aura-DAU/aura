"""
Failure Logger — PostgreSQL append-only logger for query failures and degradation.

Records queries that fail or degrade across all pipeline stages:
- Guardrail blocked (unsafe, off-topic, prompt-injection)
- Access control denied
- Retrieval empty or low-confidence abstention
- Personal / community tool execution failures
- vLLM timeouts, 429 saturation, or breaker trips
- Context budget overflows (AURA-CTX-001)
- Generation soft errors (AURA-GEN-*)

Carries langsmith_run_id to enable 1-click debugging directly from the Admin Dashboard.
Never raises on the caller's path.
"""

from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Optional

logger = logging.getLogger(__name__)


class FailureLogger:
    def __init__(self, db_module=None):
        if db_module is None:
            import db.connection as db_module
        self._db = db_module

    def record_failure(
        self,
        query_text: Optional[str] = None,
        failure_stage: Optional[str] = None,
        failure_code: Optional[str] = None,
        error_message: Optional[str] = None,
        user_role: Optional[str] = None,
        erp_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        langsmith_run_id: Optional[str] = None,
        latency_ms: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """
        Safely insert one failure record into query_failures.
        Never raises: wraps in try/except so diagnostic logging never impacts response delivery.
        """
        try:
            q = query_text if query_text is not None else kwargs.get("query", "")
            stage = failure_stage if failure_stage is not None else kwargs.get("stage", "pipeline")
            code = failure_code if failure_code is not None else kwargs.get("error_code", "UNKNOWN")
            role = user_role if user_role is not None else kwargs.get("role")
            
            trace_id = kwargs.get("trace_id") or langsmith_run_id
            trace_url = kwargs.get("trace_url")
            if not trace_url and trace_id:
                try:
                    from pipeline.tracer import get_trace_url
                    trace_url = get_trace_url(trace_id)
                except Exception as exc:
                    # Trace URL resolution failure must not disrupt failure logging
                    logger.debug("Trace URL resolution skipped: %s", exc)

            meta = dict(metadata or kwargs.get("context", {}) or {})
            if trace_url:
                meta["trace_url"] = trace_url
            if trace_id:
                meta["trace_id"] = trace_id
            meta_json = json.dumps(meta)

            self._db.execute(
                """INSERT INTO query_failures
                   (query_text, failure_stage, failure_code, error_message,
                    user_role, erp_id, thread_id, langsmith_run_id,
                    latency_ms, metadata)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)""",
                (
                    (q or "")[:4000],
                    str(stage)[:64],
                    str(code)[:64],
                    str(error_message or "")[:2000] if error_message else None,
                    str(role)[:32] if role else None,
                    str(erp_id)[:64] if erp_id else None,
                    str(thread_id)[:64] if thread_id else None,
                    str(trace_id)[:128] if trace_id else None,
                    latency_ms,
                    meta_json,
                ),
            )
        except Exception as exc:
            if "AUTH_DB_URL" in str(exc):
                logger.debug("query_failures skipped: AUTH_DB_URL not configured.")
                return
            logger.error(
                "query_failures INSERT failed — continuing.\n%s",
                traceback.format_exc(),
            )


_default_logger: Optional[FailureLogger] = None


def get_failure_logger() -> FailureLogger:
    global _default_logger
    if _default_logger is None:
        _default_logger = FailureLogger()
    return _default_logger


def record_query_failure(
    query_text: Optional[str] = None,
    failure_stage: Optional[str] = None,
    failure_code: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Convenience helper to record a query failure."""
    try:
        get_failure_logger().record_failure(
            query_text=query_text,
            failure_stage=failure_stage,
            failure_code=failure_code,
            **kwargs,
        )
    except Exception as exc:
        # Failure logging must never crash or block response delivery
        logger.debug("Failed to record query failure: %s", exc)
