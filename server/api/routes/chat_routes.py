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
from pipeline.rate_limiter import QuotaExceeded, enforce_quota

router = APIRouter(tags=["chat"])


def _resolve_request(request: ChatRequest, identity: Identity):
    history = [t.model_dump() for t in (request.history or [])][-6:]
    profile = request.resolved_profile()
    display_profile = profile.model_dump(exclude_none=True) if profile else None

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
    return history, display_profile, remaining


@router.post("/chat")
async def chat(
    request: ChatRequest,
    identity: Identity = Depends(require_identity),
):
    history, display_profile, remaining = _resolve_request(request, identity)

    async with chat_queue_lock:
        result = await run_in_threadpool(
            get_aura().ask,
            question=request.question,
            history=history,
            identity=identity.as_dict(),
            display_profile=display_profile,
        )
    if isinstance(result, dict):
        result["quota_remaining"] = remaining
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
    history, display_profile, remaining = _resolve_request(request, identity)

    loop = asyncio.get_running_loop()
    events: asyncio.Queue = asyncio.Queue()

    def on_delta(text: str) -> None:
        loop.call_soon_threadsafe(events.put_nowait, ("delta", text))

    def _run() -> None:
        try:
            result = get_aura().ask(
                question=request.question,
                history=history,
                identity=identity.as_dict(),
                display_profile=display_profile,
                on_delta=on_delta,
            )
        except Exception as exc:  # e.g. AURA init failure — never kill the stream silently
            loop.call_soon_threadsafe(events.put_nowait, ("error", str(exc)))
        else:
            loop.call_soon_threadsafe(events.put_nowait, ("done", result))

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
                    result = payload or {}
                    answer = result.get("answer", "")
                    if not streamed_any and answer:
                        yield _sse({"type": "text-delta", "delta": answer})
                    citations = []
                    for source in result.get("sources") or []:
                        if isinstance(source, dict):
                            file = source.get("file") or source.get("url") or ""
                            if file:
                                citations.append({"file": file, "title": source.get("title")})
                        elif source:
                            citations.append({"file": str(source), "title": None})
                    if citations:
                        yield _sse({"type": "citations", "citations": citations})
                    if result.get("is_personal_data"):
                        yield _sse({"type": "personal-data-flag"})
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
