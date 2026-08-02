"""
calendar_mcp_client.py -- in-process MCP client that exposes AURA's Google
Calendar MCP server (mcp_servers.gcal_server) to the agent orchestrator.

Why MCP and not a direct import of timetable_sync: the calendar-sync capability
is delivered *agentically* through the Model Context Protocol. The same
gcal_server an external MCP host could launch over stdio is connected here
in-process (the mcp SDK's in-memory transport), so the orchestrator drives the
real MCP protocol -- tool discovery + call_tool -- instead of calling the
calendar internals itself. This is the single, agentic path; the old native
sync_timetable_to_google_calendar tool has been removed.

Trust boundary (the one property the in-app JWT path gets for free): every
gcal_server tool takes `erp_id` and TRUSTS it. The model must never choose
whose calendar to write to. This adapter therefore
  1. strips `erp_id` from every tool schema shown to the model, and
  2. injects it from the verified identity at dispatch time,
discarding any erp_id the model tried to supply.

Bridging: the mcp client is async; the orchestrator is synchronous. Calendar
calls are infrequent (a student explicitly syncing), so each call runs on a
short-lived worker thread with its own event loop rather than sharing a loop or
a long-lived server session across threads.
"""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Awaitable, Callable

from mcp import Client

from mcp_servers import gcal_server

from . import service as timetable_service
from .tool_registry import Tool

logger = logging.getLogger(__name__)

# gcal_server tools that WRITE to the calendar -- tagged "write" so the
# orchestrator's confirm-before-write conventions apply. The confirm gate is
# enforced by the two-tool split (preview_* then sync_*) described in each
# tool's own MCP description, which the model sees.
_WRITE_TOOLS: frozenset[str] = frozenset(
    {"sync_timetable_to_calendar", "unsync_timetable_from_calendar"}
)

# Calendar sync is student-only -- same audience as the native tool it replaces.
_ALLOWED_ROLES: list[str] = ["student"]

_discovered: list[Tool] | None = None
_lock = threading.Lock()


def _run(make_coro: Callable[[], Awaitable[Any]]) -> Any:
    """Run an async coroutine to completion from synchronous code, whether or
    not the calling thread already has a running event loop. The coroutine is
    built inside the worker so it is bound to that thread's loop."""
    box: dict[str, Any] = {}

    def _worker() -> None:
        try:
            box["result"] = asyncio.run(make_coro())
        except BaseException as exc:  # noqa: BLE001 -- re-raised on the caller thread
            box["error"] = exc

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["result"]


async def _list_mcp_tools() -> list[Any]:
    async with Client(gcal_server.mcp) as client:
        return (await client.list_tools()).tools


async def _call_mcp_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    async with Client(gcal_server.mcp) as client:
        result = await client.call_tool(name, arguments)
    return _parse_result(name, result)


def _parse_result(name: str, result: Any) -> dict[str, Any]:
    """gcal_server tools return a dict, serialized by the MCP layer to a single
    text block (structured_content stays None because the tools aren't declared
    with structured output). Prefer structured_content if a future version sets
    it, else parse the text block."""
    structured = getattr(result, "structured_content", None)
    print("DEBUG CLIENT _parse_result structured:", structured, "content:", getattr(result, "content", None), "is_error:", getattr(result, "is_error", False))
    if isinstance(structured, dict):
        return structured

    text = result.content[0].text if getattr(result, "content", None) else ""
    if getattr(result, "is_error", False):
        return {"error": text or f"MCP tool {name} failed."}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"result": text}


def _public_schema(input_schema: dict[str, Any] | None) -> dict[str, Any]:
    """Model-facing JSON schema: the MCP tool's input schema with `erp_id`
    removed. The agent never picks whose calendar to touch -- erp_id is injected
    from the verified identity at dispatch."""
    props = {
        key: {k: v for k, v in spec.items() if k != "title"}
        for key, spec in (input_schema or {}).get("properties", {}).items()
        if key != "erp_id"
    }
    schema: dict[str, Any] = {"type": "object", "properties": props}
    required = [r for r in (input_schema or {}).get("required", []) if r != "erp_id"]
    if required:
        schema["required"] = required
    return schema


def _make_handler(tool_name: str) -> Callable[..., dict[str, Any]]:
    def handler(identity: Any, **kwargs: Any) -> dict[str, Any]:
        # Trust boundary: never let the model choose the erp_id, and ignore the
        # orchestrator's request_context (the MCP tools don't take it).
        kwargs.pop("erp_id", None)
        kwargs.pop("request_context", None)
        erp_id = timetable_service.field(identity, "erp_id")
        if not erp_id:
            return {"error": "No erp_id on the verified identity; cannot sync calendar."}
        return _run(lambda: _call_mcp_tool(tool_name, {"erp_id": erp_id, **kwargs}))

    return handler


def _build_tools() -> list[Tool]:
    try:
        mcp_tools = _run(_list_mcp_tools)
    except Exception:  # noqa: BLE001 -- calendar tools are optional; never break the agent
        logger.exception("Google Calendar MCP tool discovery failed; agent will run without them")
        return []

    return [
        Tool(
            name=t.name,
            description=t.description or "",
            parameters=_public_schema(getattr(t, "input_schema", None)),
            category="write" if t.name in _WRITE_TOOLS else "read",
            allowed_roles=list(_ALLOWED_ROLES),
            handler=_make_handler(t.name),
        )
        for t in mcp_tools
    ]


def calendar_mcp_tools() -> list[Tool]:
    """The Google Calendar MCP tools as orchestrator Tools, discovered once and
    cached. Returns [] (logged) if the MCP server can't be reached."""
    global _discovered
    if _discovered is None:
        with _lock:
            if _discovered is None:
                _discovered = _build_tools()
    return _discovered


def calendar_mcp_tools_for_role(role: str) -> list[Tool]:
    return [t for t in calendar_mcp_tools() if role in t.allowed_roles]


def calendar_mcp_registry() -> dict[str, Tool]:
    return {t.name: t for t in calendar_mcp_tools()}
