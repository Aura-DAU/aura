from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

from pipeline.exceptions import ContextLengthExceeded
from pipeline.token_budget import is_context_length_error
from pipeline.latency_tracker import get_tracker_data

logger = logging.getLogger(__name__)

# Known sentinel response strings for classification
_OFF_TOPIC = "I can only answer questions related to Dhirubhai Ambani University"
_GENERIC_DENIAL = "I'm not able to retrieve that information."
_ACADEMIC_SCOPE = "I don't have your academic programme details on file yet"
_RETRIEVAL_FAILURE = "I could not find specific information about that in the university's knowledge base."
_SAFETY_DENIAL = "violates safety, privacy, or security boundaries"
_SOFT_FAILURE = "Sorry, I encountered an error while generating a response"
_WELLNESS_NEEDLE = "Counseling Centre"


def classify_query_outcome(
    result: Optional[dict] = None,
    exc: Optional[Exception] = None,
    user_role: Optional[str] = None,
) -> tuple[str, str, Optional[str]]:
    """Determine (status, failure_stage, failure_reason) deterministically.

    Status semantics:
      - 'passed': successfully generated intended answer
      - 'failed': application, pipeline, or access failure
      - 'flagged': intentionally intercepted by safety or wellness guardrail
      - 'fallback': fallback response returned
    """
    if exc is not None:
        exc_str = str(exc)
        if isinstance(exc, ContextLengthExceeded) or is_context_length_error(exc):
            return "failed", "context_length_exceeded", "AURA-CTX-001"
        if any(kw in exc_str.lower() for kw in ["timeout", "timed out", "connection error", "exhausted"]):
            return "failed", "vllm_timeout", "VLLM_TIMEOUT"
        if "RETRIEVAL_EMPTY" in exc_str:
            return "failed", "retrieval_empty", "RETRIEVAL_EMPTY"
        if "GUARDRAIL_BLOCKED" in exc_str:
            return "flagged", "safety_guardrail", "GUARDRAIL_BLOCKED"
        return "failed", "generation_error", type(exc).__name__

    if not result or not isinstance(result, dict):
        return "failed", "generation_error", "EMPTY_RESULT"

    # Direct explicit classification attached to result dict
    if result.get("status") and result.get("failure_stage"):
        return result["status"], result["failure_stage"], result.get("failure_reason")

    answer = (result.get("answer") or "").strip()
    sources = result.get("sources") or []

    if _SAFETY_DENIAL in answer:
        return "flagged", "safety_guardrail", "UNSAFE_QUERY"

    if _OFF_TOPIC in answer:
        return "flagged", "safety_guardrail", "OFF_TOPIC"

    if _WELLNESS_NEEDLE in answer or "91372 84152" in answer or "14416" in answer:
        return "flagged", "wellness_guardrail", "WELLNESS_CRISIS"

    if answer.startswith(_GENERIC_DENIAL):
        if user_role == "guest":
            return "failed", "guest_gate", "GUEST_PERSONAL_ACCESS_DENIED"
        return "failed", "access_denied", "ACCESS_CONTROL_DENIED"

    if answer.startswith(_ACADEMIC_SCOPE):
        return "failed", "academic_scope_missing", "ACADEMIC_SCOPE_UNAVAILABLE"

    if answer.startswith(_RETRIEVAL_FAILURE) or (not sources and not result.get("is_personal_data") and not result.get("is_guardrail") and "could not find specific information" in answer):
        return "failed", "retrieval_empty", "RETRIEVAL_EMPTY"

    if answer.startswith(_SOFT_FAILURE) or "error while generating a response" in answer:
        return "failed", "generation_error", "SOFT_FAILURE_ANSWER"

    if answer.startswith("I'm experiencing a temporary connection issue") or "vllm" in answer.lower():
        return "failed", "vllm_timeout", "VLLM_TIMEOUT"

    return "passed", "none", None


def normalize_sources_for_trace(raw_sources: Optional[list]) -> tuple[list[dict], int]:
    """Extract standard source representation for query trace logs.
    [{"file": ..., "title": ..., "score": ..., "start_line": ..., "end_line": ...}]
    """
    if not raw_sources:
        return [], 0

    clean_sources: list[dict] = []
    for s in raw_sources:
        if isinstance(s, dict):
            file_path = s.get("file") or s.get("url") or s.get("path") or ""
            title = s.get("title")
            score = s.get("score") if s.get("score") is not None else s.get("rerank_score")
            start_line = s.get("start_line") or s.get("startLine")
            end_line = s.get("end_line") or s.get("endLine")
            clean_sources.append({
                "file": str(file_path),
                "title": str(title) if title is not None else None,
                "score": float(score) if isinstance(score, (int, float)) else None,
                "start_line": int(start_line) if isinstance(start_line, (int, str)) and str(start_line).isdigit() else None,
                "end_line": int(end_line) if isinstance(end_line, (int, str)) and str(end_line).isdigit() else None,
                "visibility": s.get("visibility"),
            })
        elif s:
            clean_sources.append({
                "file": str(s),
                "title": None,
                "score": None,
                "start_line": None,
                "end_line": None,
            })

    return clean_sources, len(clean_sources)


def _to_ms(seconds_val: Any) -> Optional[int]:
    if seconds_val is None:
        return None
    try:
        val = float(seconds_val)
        return max(0, int(round(val * 1000.0)))
    except (TypeError, ValueError):
        return None


def record_query_trace_sync(
    query_text: str,
    user_role: str,
    erp_id: Optional[str] = None,
    user_dept: Optional[str] = None,
    query_type: Optional[str] = None,
    status: str = "passed",
    failure_stage: Optional[str] = None,
    failure_reason: Optional[str] = None,
    sources_fetched: Optional[list] = None,
    answer_preview: Optional[str] = None,
    latency_total_ms: Optional[int] = None,
    latency_guardrail_ms: Optional[int] = None,
    latency_retrieval_ms: Optional[int] = None,
    latency_generation_ms: Optional[int] = None,
    is_personal_data: bool = False,
) -> None:
    """Execute raw DB insert synchronously. Catches all exceptions to ensure
    the calling chat request is never disrupted.
    """
    try:
        import db.connection as db_conn
    except Exception as e:
        logger.warning("[query_logger] Could not import db.connection: %s", e)
        return

    try:
        clean_sources, sources_count = normalize_sources_for_trace(sources_fetched)
        sources_json = json.dumps(clean_sources)

        # Auto-extract timings from ContextVar tracker if not explicitly passed
        tracker_data = get_tracker_data() or {}
        if latency_guardrail_ms is None and "guardrail_time" in tracker_data:
            latency_guardrail_ms = _to_ms(tracker_data["guardrail_time"])
        if latency_retrieval_ms is None and "retrieval_time" in tracker_data:
            latency_retrieval_ms = _to_ms(tracker_data["retrieval_time"])
        if latency_generation_ms is None and "generation_time" in tracker_data:
            latency_generation_ms = _to_ms(tracker_data["generation_time"])
        if latency_total_ms is None and "total_time" in tracker_data:
            latency_total_ms = _to_ms(tracker_data["total_time"])

        # Cap text fields safely to avoid unbounded memory / database bloat
        safe_query = (query_text or "").strip()[:5000]
        safe_answer = (answer_preview or "").strip()[:10000] if answer_preview else None
        safe_failure_reason = (failure_reason or "").strip()[:500] if failure_reason else None

        sql = """
            INSERT INTO query_trace_logs (
                erp_id, user_role, user_dept,
                query_text, query_type, status,
                failure_stage, failure_reason,
                sources_fetched, sources_count,
                answer_preview,
                latency_total_ms, latency_guardrail_ms,
                latency_retrieval_ms, latency_generation_ms,
                is_personal_data
            ) VALUES (
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s::jsonb, %s,
                %s,
                %s, %s,
                %s, %s,
                %s
            )
        """
        params = (
            erp_id,
            user_role or "guest",
            user_dept,
            safe_query,
            query_type or "PUBLIC",
            status,
            failure_stage or "none",
            safe_failure_reason,
            sources_json,
            sources_count,
            safe_answer,
            latency_total_ms,
            latency_guardrail_ms,
            latency_retrieval_ms,
            latency_generation_ms,
            bool(is_personal_data),
        )

        db_conn.execute(sql, params)
    except Exception as exc:
        # Non-blocking: log warning only, never raise
        logger.warning("[query_logger] Failed to write query trace log: %s", exc)


def record_query_trace_async(
    query_text: str,
    user_role: str,
    erp_id: Optional[str] = None,
    user_dept: Optional[str] = None,
    query_type: Optional[str] = None,
    status: str = "passed",
    failure_stage: Optional[str] = None,
    failure_reason: Optional[str] = None,
    sources_fetched: Optional[list] = None,
    answer_preview: Optional[str] = None,
    latency_total_ms: Optional[int] = None,
    latency_guardrail_ms: Optional[int] = None,
    latency_retrieval_ms: Optional[int] = None,
    latency_generation_ms: Optional[int] = None,
    is_personal_data: bool = False,
) -> None:
    """Non-blocking asynchronous query trace dispatch."""
    def _worker():
        record_query_trace_sync(
            query_text=query_text,
            user_role=user_role,
            erp_id=erp_id,
            user_dept=user_dept,
            query_type=query_type,
            status=status,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
            sources_fetched=sources_fetched,
            answer_preview=answer_preview,
            latency_total_ms=latency_total_ms,
            latency_guardrail_ms=latency_guardrail_ms,
            latency_retrieval_ms=latency_retrieval_ms,
            latency_generation_ms=latency_generation_ms,
            is_personal_data=is_personal_data,
        )

    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _worker)
    except RuntimeError:
        # If running outside an active event loop (e.g. sync threadpool), run directly in thread
        import threading
        t = threading.Thread(target=_worker, daemon=True)
        t.start()
