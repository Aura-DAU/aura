# POST /chat — quota-gated AURA ask via threadpool.
# POST /chat/stream — same pipeline, answer deltas streamed over SSE.
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse, StreamingResponse

from api.auth import Identity, require_identity
from api.request_context import AcademicScopeResolver, RequestContext
from api.deps import (
    chat_queue_lock,
    CHAT_QUEUE_WAIT_TIMEOUT,
    CHAT_RETRY_AFTER_SECONDS,
    get_aura,
)
from api.schemas import ChatRequest
from pipeline.exceptions import ContextLengthExceeded, RAGPipelineError
from pipeline.memory.conversation_memory import get_conversation_memory, _truncate_tokens
from pipeline.memory.user_memory import get_user_memory_store
from pipeline.memory.response_cache import get_response_cache
from pipeline.rate_limiter import QuotaExceeded, enforce_quota, _day_start
from pipeline.token_budget import is_context_length_error
from access_control import resolve_effective_role

router = APIRouter(tags=["chat"])
_scope_resolver = AcademicScopeResolver()
logger = logging.getLogger(__name__)


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


CONTEXT_LENGTH_DETAIL = (
    "This conversation is too long for AURA's context window. "
    "Try a shorter question or start a new chat."
)

PIPELINE_ERROR_DETAIL = (
    "AURA could not complete that request — please try again in a few moments."
)


def _pipeline_error_response(exc: Exception) -> JSONResponse:
    if is_context_length_error(exc):
        logger.error(
            "chat_pipeline_error code=AURA-CTX-001 status=413 exc_type=%s: %s",
            type(exc).__name__,
            exc,
        )
        return JSONResponse(
            status_code=413,
            content={"detail": CONTEXT_LENGTH_DETAIL, "code": "AURA-CTX-001"},
            headers={"Cache-Control": "no-store"},
        )

    logger.error(
        "chat_pipeline_error code=RAG_PIPELINE_ERROR status=503 exc_type=%s: %s",
        type(exc).__name__,
        exc,
        exc_info=exc,
    )
    return JSONResponse(
        status_code=503,
        content={
            "detail": PIPELINE_ERROR_DETAIL,
            "code": "RAG_PIPELINE_ERROR",
            "retryAfter": CHAT_RETRY_AFTER_SECONDS,
        },
        headers={
            "Retry-After": str(CHAT_RETRY_AFTER_SECONDS),
            "Cache-Control": "no-store",
        },
    )


async def _acquire_chat_slot() -> None:
    # Bounded backpressure: wait briefly for a concurrency slot, then shed load
    # with a retryable 503 rather than queueing unbounded under a traffic spike.
    # Caller owns the release (see _chat_slot / the streaming finally).
    try:
        await asyncio.wait_for(chat_queue_lock.acquire(), timeout=CHAT_QUEUE_WAIT_TIMEOUT)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="AURA is at peak load right now — please retry in a few seconds.",
            headers={"Retry-After": "5"},
        )


@asynccontextmanager
async def _chat_slot():
    await _acquire_chat_slot()
    try:
        yield
    finally:
        chat_queue_lock.release()


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
        now = time.time()
        seconds_to_reset = max(1, int(_day_start(now) + 86400 - now))
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({exc.limit}/day).",
            headers={"Retry-After": str(seconds_to_reset)},
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


def _conversation_capture(thread_summary: str, history: "list[dict]", question: str) -> str:
    """A compact, embeddable memory of THIS conversation for the per-user store.

    Prefers the LLM thread digest when the conversation has compacted; otherwise
    records the user's actual questions so even a short chat that never compacts
    still leaves a durable, retrievable trace. No extra LLM call — the digest is
    reused when present and the short-thread path is purely extractive."""
    thread_summary = (thread_summary or "").strip()
    questions = [
        (t.get("content") or "").strip()
        for t in (history or [])
        if t.get("role") == "user" and (t.get("content") or "").strip()
    ]
    q = (question or "").strip()
    if q:
        questions.append(q)

    if thread_summary:
        base = thread_summary
        if questions:
            base = f"{thread_summary}\nLatest question: {questions[-1]}"
    elif questions:
        base = "Questions asked: " + " | ".join(questions[-6:])
    else:
        return ""
    return _truncate_tokens(base, _env_int("AURA_CONVERSATION_CAPTURE_TOKENS", 200))


def _summary_for_generation(user_memory: str, thread_summary: str) -> str:
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

    # Cache lookup: guest public standalone queries only
    is_guest_public = (identity.role == "guest" and len(history) == 0)
    if is_guest_public:
        cache = get_response_cache()
        cached = cache.get(body.question)
        if cached:
            cached["quota_remaining"] = remaining
            return cached

    try:
        async with _chat_slot():
            result = await run_in_threadpool(
                _ask_with_memory, body, identity, history, display_profile, request_context
            )
    except RAGPipelineError as exc:
        return _pipeline_error_response(exc)
    except Exception as exc:
        # An SDK BadRequestError reaches here unwrapped whenever the 400 is
        # raised outside inference_router's rotation wrapper; everything else
        # keeps its existing 500 so genuine bugs stay loud.
        if not is_context_length_error(exc):
            raise
        return _pipeline_error_response(exc)
    if isinstance(result, dict):
        result["quota_remaining"] = remaining
        # Cache write: guest public standalone queries only (exclude error/rejection responses)
        if is_guest_public and "answer" in result and "error" not in result:
            ans = result["answer"]
            if not _is_cacheable_error_answer(ans):
                cache.set(body.question, {
                    "answer": ans,
                    "sources": result.get("sources") or []
                })
    return result


def _ask_with_memory(request, identity, history, display_profile, request_context) -> dict:
    # Compact older turns into the running summary before generating, then return
    # the updated summary + memory metadata so the (stateless) client can persist
    # the digest and advance its per-thread pointer.
    mem_result = get_conversation_memory().prepare(request.summary, history)
    user_memory_store = get_user_memory_store()
    identity_dict = identity.as_dict()
    # Inject the OTHER conversations' memory; this thread is already represented
    # by its own summary + verbatim tail, so exclude it to avoid duplication.
    user_memory = user_memory_store.get(identity_dict, exclude_thread=request.threadId)
    result = get_aura().ask(
        question=request.question,
        history=mem_result.history,
        identity=identity_dict,
        display_profile=display_profile,
        summary=_summary_for_generation(user_memory, mem_result.summary),
        request_context=request_context,
    )
    # Persist EVERY conversation (not just compacted ones), keyed by thread id so
    # this chat's block updates in place across turns. Guests no-op in the store.
    capture = _conversation_capture(mem_result.summary, mem_result.history, request.question)
    if capture:
        user_memory_store.merge(identity_dict, capture, thread_id=request.threadId)
    result = dict(result) if isinstance(result, dict) else {"answer": str(result)}
    result["memory"] = {
        "summary": mem_result.summary,
        "foldedTurns": mem_result.folded_turns,
        "summaryChanged": mem_result.summary_changed,
        "shouldFork": mem_result.should_fork,
    }
    return result


def _is_cacheable_error_answer(answer: str) -> bool:
    """True when a guest-cache write must be skipped (canned errors / abstentions)."""
    from pipeline.guardrails.query_guardrail import OFF_TOPIC_RESPONSE
    from pipeline.aura_chat import (
        GENERIC_DENIAL,
        ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE,
        RETRIEVAL_FAILURE_RESPONSE,
    )

    if not answer:
        return True
    if answer in (
        GENERIC_DENIAL,
        OFF_TOPIC_RESPONSE,
        ACADEMIC_SCOPE_UNAVAILABLE_RESPONSE,
        RETRIEVAL_FAILURE_RESPONSE,
        "I am sorry, but I cannot fulfill this request as it violates safety, privacy, or security boundaries.",
    ):
        return True
    return (
        answer.startswith("I'm having trouble retrieving")
        or answer.startswith("Sorry, I encountered an error")
        or answer.startswith("I'm experiencing a temporary connection")
        or answer.startswith("I don't have your academic programme details")
    )


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

    # Cache lookup: guest public standalone queries only
    is_guest_public = (identity.role == "guest" and len(history) == 0)
    if is_guest_public:
        cache = get_response_cache()
        cached = cache.get(body.question)
        if cached:
            async def cached_stream():
                yield _sse({"type": "quota", "remaining": remaining})
                yield _sse({"type": "text-delta", "delta": cached["answer"]})
                if cached.get("sources"):
                    yield _sse({"type": "citations", "citations": cached["sources"]})
                yield "data: [DONE]\n\n"

            headers = {
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            }
            if remaining is not None:
                headers["X-Quota-Remaining"] = str(remaining)
            return StreamingResponse(
                cached_stream(),
                media_type="text/event-stream",
                headers=headers,
            )

    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()

    def on_delta(text: str) -> None:
        loop.call_soon_threadsafe(events.put_nowait, ("delta", text))

    def on_profile_update(name: str) -> None:
        loop.call_soon_threadsafe(events.put_nowait, ("profile_update", name))

    def _run() -> None:
        try:
            mem_result = get_conversation_memory().prepare(body.summary, history)
            loop.call_soon_threadsafe(events.put_nowait, ("summary", mem_result))
            user_memory_store = get_user_memory_store()
            identity_dict = identity.as_dict()
            user_memory = user_memory_store.get(identity_dict, exclude_thread=body.threadId)
            result = get_aura().ask(
                question=body.question,
                history=mem_result.history,
                identity=identity_dict,
                display_profile=display_profile,
                on_delta=on_delta,
                on_profile_update=on_profile_update,
                summary=_summary_for_generation(user_memory, mem_result.summary),
                request_context=request_context,
            )
            # Persist every conversation, keyed by thread id (see _ask_with_memory).
            capture = _conversation_capture(mem_result.summary, mem_result.history, body.question)
            if capture:
                user_memory_store.merge(identity_dict, capture, thread_id=body.threadId)
        except Exception as exc:  # e.g. AURA init failure — never kill the stream silently
            # The exception itself, not str(exc): the consumer needs the object
            # to attribute a context overflow, whose marker often lives on the
            # wrapped __cause__ rather than in the message.
            loop.call_soon_threadsafe(events.put_nowait, ("error", exc))
        else:
            loop.call_soon_threadsafe(events.put_nowait, ("done", (result, mem_result)))

    async def event_source():
        # The concurrency slot was acquired in the endpoint (admission control),
        # so overload already failed fast with a 503 before this 200 stream began.
        # Release it when the stream ends: completion, error, or client disconnect.
        try:
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
                    if kind == "profile_update":
                        yield _sse({
                            "type": "profile-update",
                            "profile": {"name": payload}
                        })
                        continue
                    if kind == "error":
                        exc = payload if isinstance(payload, BaseException) else None
                        err_str = str(payload or "")
                        logger.error("[chat_stream] Pipeline error: %s", err_str)

                        # Classify explicit error code for developer tracing & telemetry
                        if isinstance(exc, ContextLengthExceeded) or is_context_length_error(exc):
                            # Matches the 413 code the blocking path returns, so a
                            # context overflow is attributable on both surfaces.
                            error_code = "AURA-CTX-001"
                        elif "Connection error" in err_str or "exhausted" in err_str or "Timeout" in err_str or "timeout" in err_str:
                            error_code = "VLLM_TIMEOUT"
                        elif "RETRIEVAL_EMPTY" in err_str or "No relevant documents" in err_str:
                            error_code = "RETRIEVAL_EMPTY"
                        elif "GUARDRAIL_BLOCKED" in err_str or "violates safety" in err_str:
                            error_code = "GUARDRAIL_BLOCKED"
                        else:
                            error_code = "RAG_PIPELINE_ERROR"

                        # Soft, polite user-facing message for the chat interface
                        user_msg = (
                            CONTEXT_LENGTH_DETAIL
                            if error_code == "AURA-CTX-001"
                            else "Sorry, I encountered an error while processing your request. Please try again in a few moments."
                        )

                        yield _sse({
                            "type": "error",
                            "code": error_code,
                            "detail": err_str,
                        })
                        if not streamed_any:
                            yield _sse({
                                "type": "text-delta",
                                "delta": user_msg,
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
                                    "startLine": source.get("start_line"),
                                    "endLine": source.get("end_line"),
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
                    # Inline connector prompt (e.g. "connect Google Calendar"):
                    # the orchestrator sets action_required when a tool needs an
                    # account the student hasn't linked yet. Rides the existing
                    # calendar-action SSE channel the client already parses.
                    action_required = result.get("action_required")
                    if isinstance(action_required, dict):
                        yield _sse({"type": "calendar-action", "action": action_required})
                    if mem_result is not None and mem_result.should_fork:
                        # Hard overflow: the digest itself is at capacity. Tell the
                        # client to continue in a fresh thread seeded with it.
                        yield _sse({
                            "type": "thread-continuation",
                            "summary": mem_result.summary,
                        })
                    yield _sse({"type": "quota", "remaining": remaining})

                    # Cache write: guest public standalone queries only (exclude error/rejection responses)
                    if is_guest_public and answer and "error" not in result:
                        if not _is_cacheable_error_answer(answer):
                            get_response_cache().set(body.question, {
                                "answer": answer,
                                "sources": citations
                            })

                    yield "data: [DONE]\n\n"
                    break
            finally:
                await worker
        finally:
            # Single release paired 1:1 with the single _acquire_chat_slot()
            # below. This finally runs on every exit — normal completion, error,
            # or client-disconnect cancellation — so the slot is never leaked.
            chat_queue_lock.release()

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

    # Admission control: take the concurrency slot (bounded wait → 503 on
    # overload) BEFORE returning the 200 SSE response, so peak load is a clean,
    # retryable rejection rather than a stream that dies mid-flight. The
    # event_source() finally releases the slot when the stream ends.
    await _acquire_chat_slot()
    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers=headers,
    )
