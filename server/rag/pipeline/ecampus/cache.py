"""
Short-TTL cache for scraped eCampus pages.

Scraping is slow (a real login + page fetch per call) and eCampus may not
appreciate AURA logging in on every single chat message a student sends.
This cache means "what's my attendance" twice in five minutes only scrapes
once. Swap the dict-based store for Redis in production if you're running
more than one AURA backend instance (a single process's in-memory cache
won't be shared across replicas).
"""

import time
import threading

_lock = threading.Lock()
_store: dict[str, tuple[float, object]] = {}

DEFAULT_TTL_SECONDS = 5 * 60


def cache_key(erp_id: str, page: str) -> str:
    return f"{erp_id}:{page}"


def get(key: str):
    with _lock:
        entry = _store.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if time.time() > expires_at:
            del _store[key]
            return None
        return value


def set(key: str, value, ttl_seconds: int = DEFAULT_TTL_SECONDS):
    with _lock:
        _store[key] = (time.time() + ttl_seconds, value)


def invalidate(erp_id: str):
    """Call this after any action that changes eCampus state on the
    student's behalf (none exist yet in the student-read-only phase, but
    Course Adjustments/Registration writes later would need this)."""
    with _lock:
        for k in [k for k in _store if k.startswith(f"{erp_id}:")]:
            del _store[k]
