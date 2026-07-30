"""Per-user persistent memory for cross-thread personalisation.

Thread memory remains client-owned (`summary` + tail). This store is the
backend-owned layer: when a thread gets compacted, its summary is merged into a
per-user memory blob so future threads can inherit useful preferences/facts.

Redis is used when REDIS_URL is configured; local/dev falls back to process
memory so tests and single-process runs keep working.
"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from typing import Optional, Protocol

MAX_USER_MEMORY_CHARS = 20_000
DEFAULT_USER_MEMORY_TTL_SECONDS = 90 * 24 * 60 * 60
logger = logging.getLogger(__name__)


class UserMemoryStore(Protocol):
    def get(self, identity: dict) -> str:
        pass

    def merge(
        self,
        identity: dict,
        thread_summary: str,
        previous_thread_summary: str = "",
    ) -> str:
        pass


def _identity_key(identity: dict) -> Optional[str]:
    role = identity.get("role")
    if role == "guest":
        return None
    subject = identity.get("erp_id")
    if not subject:
        return None
    digest = hashlib.sha256(f"{role}:{str(subject).lower()}".encode()).hexdigest()
    return digest


def _normalise(summary: str) -> str:
    return (summary or "").strip()


def _memory_blocks(existing: str) -> list[str]:
    existing = _normalise(existing)
    if not existing:
        return []
    blocks = []
    for raw in existing.split("## Prior Thread Memory"):
        block = _normalise(raw)
        if block:
            blocks.append(block)
    return blocks


def _merge_memory(existing: str, thread_summary: str, previous_thread_summary: str = "") -> str:
    existing = _normalise(existing)
    thread_summary = _normalise(thread_summary)
    previous_thread_summary = _normalise(previous_thread_summary)
    if not thread_summary:
        return existing

    blocks = _memory_blocks(existing)
    replaced = False
    next_blocks = []
    for block in blocks:
        if block == thread_summary:
            replaced = True
            next_blocks.append(thread_summary)
        elif previous_thread_summary and block == previous_thread_summary:
            replaced = True
            next_blocks.append(thread_summary)
        else:
            next_blocks.append(block)
    if not replaced:
        next_blocks.append(thread_summary)

    deduped = []
    seen = set()
    for block in next_blocks:
        if block in seen:
            continue
        seen.add(block)
        deduped.append(block)

    merged = "\n\n".join(f"## Prior Thread Memory\n{block}" for block in deduped)
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

    def merge(
        self,
        identity: dict,
        thread_summary: str,
        previous_thread_summary: str = "",
    ) -> str:
        key = _identity_key(identity)
        if key is None:
            return ""
        with self._lock:
            merged = _merge_memory(
                self._data.get(key, ""),
                thread_summary,
                previous_thread_summary,
            )
            self._data[key] = merged
            return merged


class RedisUserMemoryStore:
    def __init__(self, redis_url: str):
        import redis

        self._r = redis.Redis.from_url(redis_url, decode_responses=True)
        self._prefix = os.environ.get("REDIS_USER_MEMORY_PREFIX", "aura:user-memory:")
        self._ttl_seconds = _env_int(
            "REDIS_USER_MEMORY_TTL_SECONDS",
            DEFAULT_USER_MEMORY_TTL_SECONDS,
        )

    def _redis_key(self, identity: dict) -> Optional[str]:
        key = _identity_key(identity)
        return f"{self._prefix}{key}" if key else None

    def get(self, identity: dict) -> str:
        key = self._redis_key(identity)
        if key is None:
            return ""
        import redis

        try:
            return self._r.get(key) or ""
        except redis.RedisError as exc:
            logger.warning("Redis user-memory get failed for %s: %s", key, exc)
            return ""

    def merge(
        self,
        identity: dict,
        thread_summary: str,
        previous_thread_summary: str = "",
    ) -> str:
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
                        merged = _merge_memory(
                            existing,
                            thread_summary,
                            previous_thread_summary,
                        )
                        pipe.multi()
                        if self._ttl_seconds > 0:
                            pipe.set(key, merged, ex=self._ttl_seconds)
                        else:
                            pipe.set(key, merged)
                        pipe.execute()
                        return merged
                    except redis.WatchError:
                        continue
        except redis.RedisError:
            logger.warning("Redis user-memory merge failed for %s", key, exc_info=True)
            return ""


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


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
