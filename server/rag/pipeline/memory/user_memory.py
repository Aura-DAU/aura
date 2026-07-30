"""Per-user persistent memory for cross-thread personalisation.

Thread memory remains client-owned (`summary` + tail). This store is the
backend-owned layer: when a thread gets compacted, its summary is merged into a
per-user memory blob so future threads can inherit useful preferences/facts.

Redis is used when REDIS_URL is configured; local/dev falls back to process
memory so tests and single-process runs keep working.
"""

from __future__ import annotations

import hashlib
import os
import threading
from typing import Optional, Protocol

MAX_USER_MEMORY_CHARS = 20_000


class UserMemoryStore(Protocol):
    def get(self, identity: dict) -> str:
        pass

    def merge(self, identity: dict, thread_summary: str) -> str:
        pass


def _identity_key(identity: dict) -> Optional[str]:
    role = identity.get("role")
    if role == "guest":
        return None
    subject = identity.get("email") or identity.get("erp_id")
    if not subject:
        return None
    digest = hashlib.sha256(f"{role}:{str(subject).lower()}".encode()).hexdigest()
    return digest


def _normalise(summary: str) -> str:
    return (summary or "").strip()


def _merge_memory(existing: str, thread_summary: str) -> str:
    existing = _normalise(existing)
    thread_summary = _normalise(thread_summary)
    if not thread_summary:
        return existing
    if thread_summary in existing:
        return existing

    block = f"## Prior Thread Memory\n{thread_summary}"
    merged = f"{existing}\n\n{block}".strip() if existing else block
    if len(merged) <= MAX_USER_MEMORY_CHARS:
        return merged
    return merged[-MAX_USER_MEMORY_CHARS:].lstrip()


class InMemoryUserMemoryStore:
    def __init__(self):
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, identity: dict) -> str:
        key = _identity_key(identity)
        if key is None:
            return ""
        with self._lock:
            return self._data.get(key, "")

    def merge(self, identity: dict, thread_summary: str) -> str:
        key = _identity_key(identity)
        if key is None:
            return ""
        with self._lock:
            merged = _merge_memory(self._data.get(key, ""), thread_summary)
            self._data[key] = merged
            return merged


class RedisUserMemoryStore:
    def __init__(self, redis_url: str):
        import redis

        self._r = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = os.environ.get("REDIS_USER_MEMORY_PREFIX", "aura:user-memory:")

    def _redis_key(self, identity: dict) -> Optional[str]:
        key = _identity_key(identity)
        return f"{self._prefix}{key}" if key else None

    def get(self, identity: dict) -> str:
        key = self._redis_key(identity)
        if key is None:
            return ""
        return self._r.get(key) or ""

    def merge(self, identity: dict, thread_summary: str) -> str:
        key = self._redis_key(identity)
        if key is None:
            return ""
        
        import redis
        try:
            with self._r.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(key)
                        existing = pipe.get(key) or ""
                        merged = _merge_memory(existing, thread_summary)
                        pipe.multi()
                        pipe.set(key, merged)
                        pipe.execute()
                        return merged
                    except redis.WatchError:
                        continue
        except redis.RedisError:
            existing = self._r.get(key) or ""
            merged = _merge_memory(existing, thread_summary)
            self._r.set(key, merged)
            return merged


def _build_store() -> UserMemoryStore:
    redis_url = os.environ.get("REDIS_URL", "").strip()
    if redis_url:
        return RedisUserMemoryStore(redis_url)
    return InMemoryUserMemoryStore()


_shared: Optional[UserMemoryStore] = None


def get_user_memory_store() -> UserMemoryStore:
    global _shared
    if _shared is None:
        _shared = _build_store()
    return _shared


def reset_user_memory_store_for_tests(store: Optional[UserMemoryStore] = None) -> None:
    global _shared
    _shared = store if store is not None else InMemoryUserMemoryStore()
