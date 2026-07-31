"""Per-user persistent memory for cross-thread personalisation.

Thread memory remains client-owned (`summary` + tail). This store is the
backend-owned layer: every conversation contributes one *block* — keyed by its
thread id — so future threads inherit useful questions/preferences/facts even
when a chat was too short to ever compact. Blocks are kept newest-first; a new
turn for a thread replaces that thread's block in place rather than appending a
duplicate. Keying by thread id is also what makes "clear chat" mean deletion:
`delete(identity, thread_id)` drops exactly that conversation's block.

Each block is a self-contained per-conversation capture, which is exactly the
granularity Phase 2 (semantic recall over Qdrant) will embed: one point per
thread block, namespaced per user.

Redis is used when REDIS_URL is configured; local/dev falls back to process
memory so tests and single-process runs keep working.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import threading
from typing import Optional, Protocol

MAX_USER_MEMORY_CHARS = 20_000
DEFAULT_USER_MEMORY_TTL_SECONDS = 90 * 24 * 60 * 60
logger = logging.getLogger(__name__)

_BLOCK_HEADER = "## Prior Thread Memory"
# Matches a block header line, optionally carrying the storage-only thread-id
# marker (`(tid: ...)`). Legacy blobs written before id-keying have no marker and
# are parsed as anonymous blocks (id derived from their text).
_HEADER_RE = re.compile(
    r"^## Prior Thread Memory(?: \(tid: (?P<tid>[^)]*)\))?[ \t]*$",
    re.MULTILINE,
)


class UserMemoryStore(Protocol):
    def get(self, identity: dict, exclude_thread: Optional[str] = None) -> str:
        pass

    def merge(
        self,
        identity: dict,
        block: str,
        thread_id: Optional[str] = None,
    ) -> str:
        pass

    def delete(self, identity: dict, thread_id: str) -> bool:
        pass

    def delete_all(self, identity: dict) -> bool:
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


def _anon_id(text: str) -> str:
    # Stable id for blocks that arrive without a thread id (legacy blobs or a
    # client that predates threadId). Text-derived so identical captures dedupe
    # instead of piling up.
    return "anon:" + hashlib.sha1(_normalise(text).encode()).hexdigest()[:12]


def _parse_blocks(existing: str) -> list[tuple[str, str]]:
    """Storage string → ordered [(thread_id, text)], newest first (as stored)."""
    existing = _normalise(existing)
    if not existing:
        return []

    matches = list(_HEADER_RE.finditer(existing))
    if not matches:
        # No headers at all — treat the whole blob as one anonymous block.
        return [(_anon_id(existing), existing)]

    blocks: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(existing)
        text = _normalise(existing[start:end])
        if not text:
            continue
        tid = match.group("tid")
        blocks.append((tid or _anon_id(text), text))
    return blocks


def _render_storage(blocks: list[tuple[str, str]]) -> str:
    return "\n\n".join(
        f"{_BLOCK_HEADER} (tid: {tid})\n{text}" for tid, text in blocks
    )


def _render_display(blocks: list[tuple[str, str]]) -> str:
    # Prompt-facing form: clean headers, no id marker.
    return "\n\n".join(f"{_BLOCK_HEADER}\n{text}" for _tid, text in blocks)


def _cap_storage(blocks: list[tuple[str, str]]) -> str:
    rendered = _render_storage(blocks)
    if len(rendered) <= MAX_USER_MEMORY_CHARS:
        return rendered
    # Over budget: drop the oldest whole blocks (tail) first — newest memory is
    # the most useful, and unlike a raw char-slice this never leaves a block
    # truncated mid-sentence.
    while len(blocks) > 1 and len(_render_storage(blocks)) > MAX_USER_MEMORY_CHARS:
        blocks.pop()
    rendered = _render_storage(blocks)
    if len(rendered) > MAX_USER_MEMORY_CHARS and blocks:
        tid, text = blocks[0]
        header = f"{_BLOCK_HEADER} (tid: {tid})\n"
        text = text[: max(0, MAX_USER_MEMORY_CHARS - len(header))].rstrip()
        blocks[0] = (tid, text)
        rendered = _render_storage(blocks)
    return rendered


def _merge_memory(existing: str, block: str, thread_id: Optional[str] = None) -> str:
    block = _normalise(block)
    if not block:
        return _normalise(existing)

    tid = thread_id or _anon_id(block)
    blocks = _parse_blocks(existing)
    # Replace this thread's prior block (if any) and move it to the front so the
    # most recently touched conversation is injected first.
    blocks = [(t, x) for (t, x) in blocks if t != tid]
    blocks.insert(0, (tid, block))
    return _cap_storage(blocks)


def _delete_memory(existing: str, thread_id: str) -> tuple[str, bool]:
    """Drop one thread's block. Returns (remaining storage string, removed?)."""
    blocks = _parse_blocks(existing)
    kept = [(t, x) for (t, x) in blocks if t != thread_id]
    if len(kept) == len(blocks):
        return _normalise(existing), False
    return _render_storage(kept), True


def _display_from_storage(existing: str, exclude_thread: Optional[str] = None) -> str:
    blocks = _parse_blocks(existing)
    if exclude_thread:
        blocks = [(t, x) for (t, x) in blocks if t != exclude_thread]
    return _render_display(blocks)


class InMemoryUserMemoryStore:
    def __init__(self):
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()

    def get(self, identity: dict, exclude_thread: Optional[str] = None) -> str:
        key = _identity_key(identity)
        if key is None:
            return ""
        with self._lock:
            raw = self._data.get(key, "")
        return _display_from_storage(raw, exclude_thread)

    def merge(
        self,
        identity: dict,
        block: str,
        thread_id: Optional[str] = None,
    ) -> str:
        key = _identity_key(identity)
        if key is None:
            return ""
        with self._lock:
            merged = _merge_memory(self._data.get(key, ""), block, thread_id)
            self._data[key] = merged
            return merged

    def delete(self, identity: dict, thread_id: str) -> bool:
        key = _identity_key(identity)
        if key is None or not thread_id:
            return False
        with self._lock:
            remaining, removed = _delete_memory(self._data.get(key, ""), thread_id)
            if not removed:
                return False
            if remaining:
                self._data[key] = remaining
            else:
                self._data.pop(key, None)
            return True

    def delete_all(self, identity: dict) -> bool:
        key = _identity_key(identity)
        if key is None:
            return False
        with self._lock:
            return self._data.pop(key, None) is not None


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

    def get(self, identity: dict, exclude_thread: Optional[str] = None) -> str:
        key = self._redis_key(identity)
        if key is None:
            return ""
        import redis

        try:
            raw = self._r.get(key) or ""
        except redis.RedisError as exc:
            logger.warning("Redis user-memory get failed for %s: %s", key, exc)
            return ""
        return _display_from_storage(raw, exclude_thread)

    def merge(
        self,
        identity: dict,
        block: str,
        thread_id: Optional[str] = None,
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
                        merged = _merge_memory(existing, block, thread_id)
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

    def delete(self, identity: dict, thread_id: str) -> bool:
        """Remove one conversation's block. Same WATCH/MULTI retry as merge, so a
        concurrent merge for another thread cannot be lost by this rewrite."""
        key = self._redis_key(identity)
        if key is None or not thread_id:
            return False

        import redis
        try:
            with self._r.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch(key)
                        existing = pipe.get(key) or ""
                        remaining, removed = _delete_memory(existing, thread_id)
                        if not removed:
                            pipe.unwatch()
                            return False
                        # Preserve the key's remaining retention rather than
                        # restarting the 90-day clock on the surviving blocks.
                        ttl = pipe.ttl(key)
                        pipe.multi()
                        if not remaining:
                            pipe.delete(key)
                        elif isinstance(ttl, int) and ttl > 0:
                            pipe.set(key, remaining, ex=ttl)
                        elif self._ttl_seconds > 0:
                            pipe.set(key, remaining, ex=self._ttl_seconds)
                        else:
                            pipe.set(key, remaining)
                        pipe.execute()
                        return True
                    except redis.WatchError:
                        continue
        except redis.RedisError:
            logger.warning("Redis user-memory delete failed for %s", key, exc_info=True)
            return False

    def delete_all(self, identity: dict) -> bool:
        key = self._redis_key(identity)
        if key is None:
            return False

        import redis
        try:
            return bool(self._r.delete(key))
        except redis.RedisError:
            logger.warning("Redis user-memory delete_all failed for %s", key, exc_info=True)
            return False


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
