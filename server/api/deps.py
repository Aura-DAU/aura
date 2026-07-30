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
_chat_limit = max(1, int(os.getenv("CHAT_CONCURRENCY", "4")))
chat_queue_lock = asyncio.Semaphore(_chat_limit)


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
