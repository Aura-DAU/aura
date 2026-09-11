"""
LangSmith Tracer — Config, callback handling, and LLM instrumentation for AURA.

Enables end-to-end distributed tracing across:
1. LangGraph Agent Orchestrator (AuraChatGraph)
2. Tool execution / EcampusOrchestrator
3. vLLM LLM calls dispatched through InferenceRouter

Fails completely silent / no-op if LANGCHAIN_API_KEY or LANGSMITH_API_KEY is not set.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_PROJECT = "aura-dau"


def is_tracing_enabled() -> bool:
    """Return True if LangSmith tracing is actively configured in the environment."""
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    tracing_flag = (
        os.getenv("LANGSMITH_TRACING")
        or os.getenv("LANGCHAIN_TRACING_V2")
        or ""
    ).strip().lower()
    return bool(api_key and tracing_flag in ("1", "true", "yes", "on"))


def get_project_name() -> str:
    """Return the active LangSmith project name."""
    return (
        os.getenv("LANGSMITH_PROJECT")
        or os.getenv("LANGCHAIN_PROJECT")
        or _DEFAULT_PROJECT
    ).strip()


def get_langsmith_run_url(run_id: Optional[str]) -> Optional[str]:
    """Generate the direct LangSmith web UI link for a specific run ID."""
    if not run_id:
        return None
    project = get_project_name()
    return f"https://smith.langchain.com/o/default/projects/p/{project}/r/{run_id}"


try:
    from langchain_core.callbacks import BaseCallbackHandler

    class RootRunCollector(BaseCallbackHandler):
        """Captures the root execution run ID from LangGraph for attribution and error tracking."""

        def __init__(self) -> None:
            super().__init__()
            self.run_id: Optional[str] = None

        def on_chain_start(
            self,
            serialized: dict[str, Any],
            inputs: dict[str, Any],
            *,
            run_id: Any,
            **kwargs: Any,
        ) -> None:
            if self.run_id is None:
                self.run_id = str(run_id)

        def on_chain_error(
            self,
            error: BaseException,
            *,
            run_id: Any,
            **kwargs: Any,
        ) -> None:
            if self.run_id is None:
                self.run_id = str(run_id)

except Exception:
    class RootRunCollector:  # type: ignore
        def __init__(self) -> None:
            self.run_id = None


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
    Returns (run_config, collector) where collector.run_id will hold the root run UUID.
    """
    collector = RootRunCollector()
    full_meta = dict(metadata or {})
    if thread_id:
        full_meta["thread_id"] = thread_id
    if erp_id:
        full_meta["erp_id"] = erp_id
    if role:
        full_meta["role"] = role

    full_tags = list(tags or [])
    if role and role not in full_tags:
        full_tags.append(role)

    config: dict[str, Any] = {
        "run_name": run_name,
        "callbacks": [collector],
        "metadata": full_meta,
        "tags": full_tags,
    }
    return config, collector


def wrap_openai_client(client: Any) -> Any:
    """
    Wrap an openai.OpenAI client instance with LangSmith's tracer if tracing is enabled.
    Guaranteed never to throw; falls back to original client.
    """
    if not is_tracing_enabled():
        return client
    try:
        from langsmith.wrappers import wrap_openai
        return wrap_openai(client)
    except Exception as exc:
        logger.warning("Failed to wrap OpenAI client with LangSmith: %s", exc)
        return client
