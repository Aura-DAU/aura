# Shared FastAPI dependencies (lazy AURA init, speech concurrency).
import asyncio
import threading

_aura = None
_aura_lock = threading.Lock()

# Serialize Whisper jobs — concurrent ffmpeg/transcription is expensive.
speech_queue_lock = asyncio.Semaphore(1)


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
