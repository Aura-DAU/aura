"""
Chat History Logger — PostgreSQL store for conversation threads and messages.

Persists completed user-assistant chat turns to:
- chat_threads
- chat_messages

Enables admins to audit conversations and inspect full multi-turn dialogs
leading up to errors or bad answers.
Never raises on the caller's path.
"""

from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ChatHistoryLogger:
    def __init__(self, db_module=None):
        if db_module is None:
            import db.connection as db_module
        self._db = db_module

    def record_turn(
        self,
        thread_id: str,
        erp_id: Optional[str],
        role: str,
        user_message: str,
        assistant_message: str,
        sources: Optional[list[Any]] = None,
        is_personal_data: bool = False,
        trace_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Record a completed conversation turn (both user query and assistant reply).
        Safely creates or updates the thread and inserts both messages.
        """
        if not thread_id:
            return

        run_id = trace_id or kwargs.get("langsmith_run_id")

        try:
            # Generate a helpful thread title from the initial user query (first 60 chars)
            clean_q = (user_message or "").strip().replace("\n", " ")
            title = (clean_q[:60] + "...") if len(clean_q) > 60 else (clean_q or "New Chat")

            # 1. Upsert thread
            self._db.execute(
                """INSERT INTO chat_threads (id, erp_id, role, title, last_activity)
                   VALUES (%s, %s, %s, %s, now())
                   ON CONFLICT (id) DO UPDATE
                   SET last_activity = now(),
                       title = CASE
                           WHEN chat_threads.title IN ('New Chat', '') AND EXCLUDED.title NOT IN ('New Chat', '')
                           THEN EXCLUDED.title
                           ELSE chat_threads.title
                       END""",
                (thread_id, erp_id, role or "student", title),
            )

            # 2. Insert user message
            self._db.execute(
                """INSERT INTO chat_messages (thread_id, role, content, is_personal_data, sources)
                   VALUES (%s, 'user', %s, FALSE, '[]'::jsonb)""",
                (thread_id, user_message),
            )

            # 3. Insert assistant message
            sources_json = json.dumps(sources or [])
            self._db.execute(
                """INSERT INTO chat_messages (thread_id, role, content, is_personal_data, sources, langsmith_run_id)
                   VALUES (%s, 'assistant', %s, %s, %s::jsonb, %s)""",
                (thread_id, assistant_message, is_personal_data, sources_json, run_id),
            )
        except Exception as exc:
            if "AUTH_DB_URL" in str(exc):
                logger.debug("chat_history skipped: AUTH_DB_URL not configured.")
                return
            logger.error(
                "chat_history INSERT failed for thread %s — continuing.\n%s",
                thread_id,
                traceback.format_exc(),
            )


_default_history_logger: Optional[ChatHistoryLogger] = None


def get_chat_history_logger() -> ChatHistoryLogger:
    global _default_history_logger
    if _default_history_logger is None:
        _default_history_logger = ChatHistoryLogger()
    return _default_history_logger


def record_chat_turn(
    thread_id: Optional[str],
    erp_id: Optional[str],
    role: str,
    user_message: str,
    assistant_message: str,
    sources: Optional[list[Any]] = None,
    is_personal_data: bool = False,
    trace_id: Optional[str] = None,
    **kwargs: Any,
) -> None:
    """Convenience helper to record a completed chat turn."""
    if not thread_id:
        return
    try:
        get_chat_history_logger().record_turn(
            thread_id=thread_id,
            erp_id=erp_id,
            role=role,
            user_message=user_message,
            assistant_message=assistant_message,
            sources=sources,
            is_personal_data=is_personal_data,
            trace_id=trace_id,
            **kwargs,
        )
    except Exception:
        pass
