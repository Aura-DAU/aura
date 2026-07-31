# Shared FastAPI dependencies (lazy AURA init, speech/chat concurrency).
import asyncio
import os
import threading

_aura = None
_aura_lock = threading.Lock()

# Serialize Whisper jobs — concurrent ffmpeg/transcription is expensive.
speech_queue_lock = asyncio.Semaphore(1)

# Cap concurrent RAG/LLM asks so a burst of authenticated users cannot pin
# every worker on long-running inference. Override via CHAT_CONCURRENCY.
#
# IMPORTANT — this limit is PER uvicorn worker process, not global cluster
# capacity. Total admitted ≈ CHAT_CONCURRENCY × BACKEND_WORKERS × api_replicas.
#
# Size CHAT_CONCURRENCY against the LIVE per-node `num_requests_running`
# ceiling × healthy endpoint count — NOT against a compose default. Compose
# currently passes `--max-num-seqs ${VLLM_MAX_NUM_SEQS:-64}` but live nodes
# have been observed at 24 (neither the compose default nor vLLM's own 256),
# and a rebuild from the repo would produce 64-slot nodes whose KV cache
# cannot actually back that many concurrent long RAG prompts. Pin
# VLLM_MAX_NUM_SEQS explicitly in the env examples before trusting any
# arithmetic derived from it.
#
# Worked examples against today's measured live ceiling of 24 running/node
# (each ask fires multiple LLM calls so effective demand > 1 slot/ask):
#   - Verified 3 healthy endpoints: 3 × 24 = 72 GPU slots → CHAT_CONCURRENCY=24
#     with BACKEND_WORKERS=4 (≈96 admitted/replica) is ~1.3× and acceptable.
#   - Single-node reality (GPU-01 pin / GPU-04 one-endpoint pool): 24 GPU
#     slots → prefer CHAT_CONCURRENCY=6 (≈24 admitted) until the pool is
#     verified multi-node; 8 is the upper bound before over-admission.
# Default stays conservative for local/dev single-process runs.
CHAT_CONCURRENCY = max(1, int(os.getenv("CHAT_CONCURRENCY", "4")))
_chat_limit = CHAT_CONCURRENCY
chat_queue_lock = asyncio.Semaphore(_chat_limit)

# Load-shedding budget: how long a request may WAIT for a concurrency slot
# before it's rejected with a retryable 503 instead of queueing unbounded. Under
# a 1000-user burst the semaphore's waiter queue would otherwise grow without
# bound — every waiter pinning a socket + request buffers — until the event loop
# starves or the process OOMs. Keep this SHORT (default 2s) so overload fails
# fast with Retry-After instead of looking like a hang. Tune via env.
CHAT_QUEUE_WAIT_TIMEOUT = float(os.getenv("CHAT_QUEUE_WAIT_TIMEOUT", "2"))

# Seconds the client is told to wait before retrying a shed ask. Kept in one
# place so the 503 header, the JSON body, and the edge's matching Retry-After
# stay aligned.
CHAT_RETRY_AFTER_SECONDS = 5


def get_aura():
    # Defer heavy Pinecone/embedding import until first /chat.
    global _aura
    if _aura is None:
        with _aura_lock:
            if _aura is None:
                from rag import AURA  # noqa: PLC0415 — deferred heavy import
                _aura = AURA()
    return _aura


def warm_aura_in_background() -> None:
    # Without warm-up the first /chat after boot pays the full embedding +
    # reranker + Pinecone init (tens of seconds). Daemon thread so startup
    # and serving are never blocked; a /chat arriving mid-warm-up simply
    # waits on _aura_lock and reuses the same instance.
    def _warm() -> None:
        try:
            get_aura()
            print("[deps] AURA warm-up complete.")
        except Exception as exc:
            print(f"[deps] AURA warm-up failed (will lazy-init on first /chat): {exc}")

    threading.Thread(target=_warm, name="aura-warmup", daemon=True).start()
