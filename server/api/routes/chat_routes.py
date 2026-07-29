# POST /chat — quota-gated AURA ask via threadpool.
# POST /chat/stream — same pipeline, answer deltas streamed over SSE.
import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from api.auth import Identity, require_identity
from api.deps import chat_queue_lock, get_aura
from api.schemas import ChatRequest
from pipeline.memory.conversation_memory import get_conversation_memory
from pipeline.rate_limiter import QuotaExceeded, enforce_quota

router = APIRouter(tags=["chat"])


def _resolve_request(request: ChatRequest, identity: Identity):
    # No fixed truncation: ConversationMemory.prepare() budgets the full tail
    # against the model window and folds the overflow into the summary. Pydantic
    # already caps history at 20 turns (schemas.ChatRequest).
    history = [t.model_dump() for t in (request.history or [])]
    profile = request.resolved_profile()
    display_profile = profile.model_dump(exclude_none=True) if profile else None

    quota_key = identity.email or identity.erp_id
    try:
        enforce_quota(quota_key, identity.role)
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({exc.limit}/day).",
        ) from exc
    return history, display_profile


@router.post("/chat")
async def chat(
    request: ChatRequest,
    identity: Identity = Depends(require_identity),
):
    history, display_profile = _resolve_request(request, identity)

    async with chat_queue_lock:
        return await run_in_threadpool(
            _ask_with_memory, request, identity, history, display_profile
        )


def _ask_with_memory(request, identity, history, display_profile) -> dict:
    # Compact older turns into the running summary before generating, then return
    # the updated summary + memory metadata so the (stateless) client can persist
    # the digest and advance its per-thread pointer.
    mem_result = get_conversation_memory().prepare(request.summary, history)
    result = get_aura().ask(
        question=request.question,
        history=mem_result.history,
        identity=identity.as_dict(),
        display_profile=display_profile,
        summary=mem_result.summary,
    )
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
    request: ChatRequest,
    identity: Identity = Depends(require_identity),
):
    # Emits the SSE event shapes the Next.js client already parses
    # (text-delta / citations / personal-data-flag / [DONE]), so the frontend
    # proxy route can pipe the body through untouched. Quota and auth errors
    # are raised before streaming starts and reach the client as real HTTP
    # status codes.
    history, display_profile = _resolve_request(request, identity)

    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()

    def on_delta(text: str) -> None:
        loop.call_soon_threadsafe(events.put_nowait, ("delta", text))

    def _run() -> None:
        try:
            mem_result = get_conversation_memory().prepare(request.summary, history)
            loop.call_soon_threadsafe(events.put_nowait, ("summary", mem_result))
            result = get_aura().ask(
                question=request.question,
                history=mem_result.history,
                identity=identity.as_dict(),
                display_profile=display_profile,
                on_delta=on_delta,
                summary=mem_result.summary,
            )
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
                    result = result or {}
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
                                citations.append({
                                    "file": file,
                                    "title": source.get("title"),
                                    "path": source.get("path"),
                                    "start_line": source.get("start_line"),
                                    "end_line": source.get("end_line"),
                                    "visibility": source.get("visibility"),
                                    "authorization": source.get("authorization"),
                                })
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
                    yield "data: [DONE]\n\n"
                    break
            finally:
                await worker

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )
