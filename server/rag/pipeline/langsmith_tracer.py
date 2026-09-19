"""
Backwards-compatibility wrapper for langsmith_tracer.py.

All implementations have migrated to the unified, open-source-first
`pipeline.tracer` module (supporting Langfuse, LangSmith, and local execution).
"""

from __future__ import annotations

from pipeline.tracer import (
    is_tracing_enabled,
    get_project_name,
    get_langsmith_run_url,
    get_langfuse_trace_url,
    get_trace_url,
    get_active_provider,
    create_trace_config,
    wrap_openai_client,
    RootRunCollector,
)

__all__ = [
    "is_tracing_enabled",
    "get_project_name",
    "get_langsmith_run_url",
    "get_langfuse_trace_url",
    "get_trace_url",
    "get_active_provider",
    "create_trace_config",
    "wrap_openai_client",
    "RootRunCollector",
]
