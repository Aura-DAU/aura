# POST /chat — quota-gated AURA ask via threadpool.
# POST /chat/stream — same pipeline, answer deltas streamed over SSE.
import asyncio
import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from api.auth import Identity, require_identity
from api.request_context import AcademicScopeResolver, RequestContext
from api.deps import chat_queue_lock, get_aura
from api.schemas import ChatRequest
from pipeline.memory.conversation_memory import get_conversation_memory
from pipeline.memory.user_memory import get_user_memory_store
from pipeline.rate_limiter import QuotaExceeded, enforce_quota
from access_control import resolve_effective_role

router = APIRouter(tags=["chat"])
_scope_resolver = AcademicScopeResolver()
logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


def _resolve_request(body: ChatRequest, identity: Identity, req: Request):
    # No fixed truncation: ConversationMemory.prepare() budgets the full tail
    # against the model window and folds the overflow into the summary. Pydantic
    # already caps history at 20 turns (schemas.ChatRequest).
    history = [t.model_dump() for t in (body.history or [])]
    profile = body.resolved_profile()
    display_profile = profile.model_dump(exclude_none=True) if profile else None

    if identity.role == "guest":
        # Guests have no email, but Next.js mints a stable anonymous erp_id
        # per browser (stored in a cookie) specifically so each guest gets
        # their own quota bucket — see rate_limiter.py's module docstring.
        # Keying by IP instead (the old behavior) put every guest behind
        # the same NAT/campus Wi-Fi/mobile carrier into one shared bucket,
        # so one guest's questions could exhaust another's quota and trip
        # a 429 long before that guest's own 10 questions were used.
        quota_key = identity.erp_id
    else:
        quota_key = identity.email or identity.erp_id

    try:
        remaining = enforce_quota(quota_key, identity.role)
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({exc.limit}/day).",
        ) from exc
    # `remaining` (None for unlimited roles) is the server's authoritative
    # count. Callers surface it back to the client on every response so the
    # UI counter can never silently drift from what the server will actually
    # enforce (see aura/hooks/use-aura-chat.ts).

    try:
        effective_role = resolve_effective_role(identity)
    except Exception as exc:
        logger.warning("Effective role resolution failed for %s: %s", identity.erp_id, exc)
        effective_role = identity.role

    try:
        request_context = _scope_resolver.resolve(identity, effective_role)
    except Exception as exc:
        logger.warning("Request context resolution failed for %s: %s", identity.erp_id, exc)
        request_context = RequestContext(
            identity=identity,
            effective_role=effective_role,
            academic_scope=None,
        )
    return history, display_profile, request_context, remaining


def _summary_for_generation(user_memory: str, thread_summary: str) -> str:
    from pipeline.memory.conversation_memory import _truncate_tokens

    conversation_memory = get_conversation_memory()
    thread_summary = _truncate_tokens(thread_summary or "", conversation_memory.summary_max_tokens)
    user_memory_tokens = _env_int("AURA_USER_MEMORY_TOKENS", 400)

    parts = []
    if user_memory:
        user_memory = _truncate_tokens(user_memory, user_memory_tokens)
        if user_memory:
            parts.append("Persistent User Memory\n" + user_memory)
    if thread_summary:
        parts.append("Current Thread Summary\n" + thread_summary)
    return "\n\n".join(parts)


@router.post("/chat")
async def chat(
    req: Request,
    body: ChatRequest,
    identity: Identity = Depends(require_identity),
):
    history, display_profile, request_context, remaining = _resolve_request(body, identity, req)

    async with chat_queue_lock:
        result = await run_in_threadpool(
            _ask_with_memory, body, identity, history, display_profile, request_context
        )
    if isinstance(result, dict):
        result["quota_remaining"] = remaining
    return result


def _ask_with_memory(request, identity, history, display_profile, request_context) -> dict:
    # Compact older turns into the running summary before generating, then return
    # the updated summary + memory metadata so the (stateless) client can persist
    # the digest and advance its per-thread pointer.
    mem_result = get_conversation_memory().prepare(request.summary, history)
    user_memory_store = get_user_memory_store()
    identity_dict = identity.as_dict()
    user_memory = user_memory_store.get(identity_dict)
    result = get_aura().ask(
        question=request.question,
        history=mem_result.history,
        identity=identity_dict,
        display_profile=display_profile,
        summary=_summary_for_generation(user_memory, mem_result.summary),
        request_context=request_context,
    )
    if mem_result.summary_changed:
        user_memory_store.merge(identity_dict, mem_result.summary, request.summary or "")
    result = dict(result) if isinstance(result, dict) else {"answer": str(result)}
    result["memory"] = {
        "summary": mem_result.summary,
        "foldedTurns": mem_result.folded_turns,
        "summaryChanged": mem_result.summary_changed,
        "shouldFork": mem_result.should_fork,
    }
    return result


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


@router.post("/chat/stream")
async def chat_stream(
    req: Request,
    body: ChatRequest,
    identity: Identity = Depends(require_identity),
):
    # Emits the SSE event shapes the Next.js client already parses
    # (text-delta / citations / personal-data-flag / [DONE]), so the frontend
    # proxy route can pipe the body through untouched. Quota and auth errors
    # are raised before streaming starts and reach the client as real HTTP
    # status codes.
    history, display_profile, request_context, remaining = _resolve_request(body, identity, req)

    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()

    def on_delta(text: str) -> None:
        loop.call_soon_threadsafe(events.put_nowait, ("delta", text))

    def _run() -> None:
        try:
            mem_result = get_conversation_memory().prepare(body.summary, history)
            loop.call_soon_threadsafe(events.put_nowait, ("summary", mem_result))
            user_memory_store = get_user_memory_store()
            identity_dict = identity.as_dict()
            user_memory = user_memory_store.get(identity_dict)
            result = get_aura().ask(
                question=body.question,
                history=mem_result.history,
                identity=identity_dict,
                display_profile=display_profile,
                on_delta=on_delta,
                summary=_summary_for_generation(user_memory, mem_result.summary),
                request_context=request_context,
            )
            if mem_result.summary_changed:
                user_memory_store.merge(identity_dict, mem_result.summary, body.summary or "")
        except Exception as exc:  # e.g. AURA init failure — never kill the stream silently
            loop.call_soon_threadsafe(events.put_nowait, ("error", str(exc)))
        else:
            loop.call_soon_threadsafe(events.put_nowait, ("done", (result, mem_result)))

    async def event_source():
        # Hold a concurrency slot for the whole stream so authenticated
        # floods cannot open unbounded parallel RAG/LLM jobs.
        async with chat_queue_lock:
            # to_thread copies contextvars, so latency_tracker segments recorded
            # inside the pipeline still land in this request's middleware dict.
            worker = asyncio.create_task(asyncio.to_thread(_run))
            streamed_any = False
            try:
                while True:
                    kind, payload = await events.get()
                    if kind == "delta":
                        streamed_any = True
                        yield _sse({"type": "text-delta", "delta": payload})
                        continue
                    if kind == "summary":
                        # Compaction ran before generation. Tell the client the
                        # new digest and how many turns were folded so it can
                        # persist the summary and advance its history pointer.
                        if payload.summary_changed:
                            yield _sse({
                                "type": "summary-update",
                                "summary": payload.summary,
                                "foldedTurns": payload.folded_turns,
                            })
                        continue
                    if kind == "error":
                        print(f"[chat_stream] pipeline error: {payload}")
                        if not streamed_any:
                            yield _sse({
                                "type": "text-delta",
                                "delta": "Sorry, I encountered an error while generating a response. Please try again.",
                            })
                        yield "data: [DONE]\n\n"
                        break
                    # done — canned/denial paths stream nothing, so emit the whole
                    # answer as a single delta to match the non-streaming UX.
                    result, mem_result = payload if payload else ({}, None)
                    result = dict(result) if isinstance(result, dict) else {"answer": str(result)}
                    answer = result.get("answer", "")
                    if not streamed_any and answer:
                        yield _sse({"type": "text-delta", "delta": answer})
                    citations = []
                    for source in result.get("sources") or []:
                        if isinstance(source, dict):
                            file = source.get("file") or source.get("url") or source.get("path") or ""
                            if file:
                                # Forward the full citation shape (not just
                                # file/title) so the frontend can render the
                                # clickable document side-drawer and auth badge
                                # for streamed answers, matching the blocking path.
                                citation_obj = {
                                    "file": file,
                                    "title": source.get("title"),
                                    "path": source.get("path"),
                                    "start_line": source.get("start_line"),
                                    "end_line": source.get("end_line"),
                                    "visibility": source.get("visibility"),
                                    "authorization": source.get("authorization"),
                                }
                                citations.append({k: v for k, v in citation_obj.items() if v is not None})
                        elif source:
                            citations.append({"file": str(source), "title": None})
                    if citations:
                        yield _sse({"type": "citations", "citations": citations})
                    if result.get("is_personal_data"):
                        yield _sse({"type": "personal-data-flag"})
                    if mem_result is not None and mem_result.should_fork:
                        # Hard overflow: the digest itself is at capacity. Tell the
                        # client to continue in a fresh thread seeded with it.
                        yield _sse({
                            "type": "thread-continuation",
                            "summary": mem_result.summary,
                        })
                    yield _sse({"type": "quota", "remaining": remaining})
                    yield "data: [DONE]\n\n"
                    break
            finally:
                await worker

    headers = {
        "Cache-Control": "no-cache, no-transform",
        "X-Accel-Buffering": "no",
    }
    # Set even though the body streams the same value as a "quota" event —
    # some proxies/clients read remaining-quota from headers before the
    # body is fully parsed. `remaining` is known upfront since enforce_quota
    # already ran in _resolve_request, before any streaming starts.
    if remaining is not None:
        headers["X-Quota-Remaining"] = str(remaining)

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers=headers,
    )