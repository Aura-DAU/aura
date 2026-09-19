"""
Unified Telemetry & Tracing Module for AURA.

Supports:
1. Langfuse (Recommended Free & Open-Source alternative):
   - Configured via LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST.
   - Works with Langfuse Cloud (free 50k traces/mo) or self-hosted Docker container.
2. LangSmith (Legacy fallback):
   - Configured via LANGSMITH_API_KEY / LANGCHAIN_API_KEY.
3. Local/Silent Fallback:
   - When no external tracing service is configured, operates silently with zero
     overhead, generating local trace IDs for consistent incident and conversation correlation.
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_PROJECT = "aura-dau"


def get_active_provider() -> str:
    """
    Determine the active tracing provider from environment variables:
    - 'langfuse': If LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set.
    - 'langsmith': If LANGSMITH_API_KEY or LANGCHAIN_API_KEY is configured with tracing enabled.
    - 'none': When no external tracing backend is active.
    """
    if os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"):
        return "langfuse"

    smith_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    smith_flag = (
        os.getenv("LANGSMITH_TRACING")
        or os.getenv("LANGCHAIN_TRACING_V2")
        or ""
    ).strip().lower()
    if smith_key and smith_flag in ("1", "true", "yes", "on"):
        return "langsmith"

    return "none"


def is_tracing_enabled() -> bool:
    """Return True if an external tracing provider (Langfuse or LangSmith) is configured."""
    return get_active_provider() != "none"


def get_project_name() -> str:
    """Return the active tracing project name."""
    return (
        os.getenv("LANGFUSE_PROJECT_ID")
        or os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or _DEFAULT_PROJECT
    ).strip()


def get_langfuse_trace_url(trace_id: Optional[str]) -> Optional[str]:
    """Generate the direct web UI URL for a Langfuse trace."""
    if not trace_id:
        return None
    host = (os.getenv("LANGFUSE_HOST") or "https://cloud.langfuse.com").rstrip("/")
    project_id = os.getenv("LANGFUSE_PROJECT_ID", "").strip()
    if project_id:
        return f"{host}/project/{project_id}/traces/{trace_id}"
    return f"{host}/trace/{trace_id}"


def get_langsmith_run_url(run_id: Optional[str]) -> Optional[str]:
    """Generate the direct LangSmith web UI link for a specific run ID."""
    if not run_id:
        return None
    project = (
        os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or _DEFAULT_PROJECT
    ).strip()
    return f"https://smith.langchain.com/o/default/projects/p/{project}/r/{run_id}"


def get_trace_url(trace_id: Optional[str]) -> Optional[str]:
    """
    Generate the direct web UI URL for the active tracing provider.
    Returns None if tracing is disabled or trace_id is empty.
    """
    if not trace_id:
        return None
    provider = get_active_provider()
    if provider == "langfuse":
        return get_langfuse_trace_url(trace_id)
    elif provider == "langsmith":
        return get_langsmith_run_url(trace_id)
    return None


try:
    from langchain_core.callbacks import BaseCallbackHandler
except Exception:
    class BaseCallbackHandler:  # type: ignore
        pass


class RootRunCollector(BaseCallbackHandler):
    """
    Captures or generates the root trace UUID for attribution, error tracking,
    and deep-linking across LangGraph, Langfuse, LangSmith, and PostgreSQL logs.
    """

    def __init__(self, trace_id: Optional[str] = None) -> None:
        super().__init__()
        self.run_id: Optional[str] = trace_id or str(uuid.uuid4())

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        if run_id:
            self.run_id = str(run_id)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Any,
        **kwargs: Any,
    ) -> None:
        if run_id and not self.run_id:
            self.run_id = str(run_id)


def create_trace_config(
    run_name: str = "aura_chat_graph",
    thread_id: Optional[str] = None,
    erp_id: Optional[str] = None,
    role: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    tags: Optional[list[str]] = None,
) -> Tuple[dict[str, Any], RootRunCollector]:
    """
    Build a runnable config dictionary for LangGraph .invoke() or runnable executions.
    Returns (run_config, collector) where collector.run_id will hold the root trace UUID.
    """
    trace_uuid = str(uuid.uuid4())
    collector = RootRunCollector(trace_id=trace_uuid)

    full_meta = dict(metadata or {})
    if thread_id:
        full_meta["thread_id"] = thread_id
    if erp_id:
        full_meta["erp_id"] = erp_id
    if role:
        full_meta["role"] = role
    full_meta["trace_id"] = trace_uuid

    full_tags = list(tags or [])
    if role and role not in full_tags:
        full_tags.append(role)

    callbacks: list[Any] = [collector]

    provider = get_active_provider()
    if provider == "langfuse":
        try:
            from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
            lf_handler = LangfuseCallbackHandler(
                public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
                host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                session_id=thread_id,
                user_id=erp_id,
                metadata=full_meta,
                tags=full_tags,
                trace_name=run_name,
            )
            callbacks.append(lf_handler)
        except Exception as exc:
            logger.debug("Langfuse callback handler initialization skipped: %s", exc)

    config: dict[str, Any] = {
        "run_name": run_name,
        "callbacks": callbacks,
        "metadata": full_meta,
        "tags": full_tags,
    }
    return config, collector


def wrap_openai_client(client: Any) -> Any:
    """
    Wrap an openai.OpenAI client instance with the active tracer (Langfuse or LangSmith).
    Guaranteed never to throw; falls back safely to original client.
    """
    provider = get_active_provider()
    if provider == "langfuse":
        try:
            from langfuse.openai import wrap_openai
            return wrap_openai(client)
        except Exception as exc:
            logger.debug("Langfuse OpenAI wrapper skipped: %s", exc)
            return client
    elif provider == "langsmith":
        try:
            from langsmith.wrappers import wrap_openai
            return wrap_openai(client)
        except Exception as exc:
            logger.debug("LangSmith OpenAI wrapper skipped: %s", exc)
            return client
    return client
