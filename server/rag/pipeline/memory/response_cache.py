import os
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ResponseCache:
    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL", "").strip()
        self._prefix = "aura:public-cache:"
        self._ttl_seconds = 86400  # Default 24 hours (automatic expiration)
        self._r = None
        
        if self.redis_url:
            try:
                import redis
                self._r = redis.Redis.from_url(self.redis_url, decode_responses=True)
            except Exception as e:
                logger.warning("Failed to initialize Redis for response cache: %s", e)

    def _key(self, query: str) -> str:
        import hashlib
        import re
        # Collapse whitespace + casefold, then strip trailing sentence punctuation
        # so "hostel rules?" and "hostel rules" share a cache entry. Guests are
        # the highest-volume path and the only consumers of this cache; do not
        # strip leading question words here — that would conflate distinct asks
        # ("what is X" vs "why is X").
        cleaned = " ".join(query.strip().lower().split())
        cleaned = re.sub(r"[?!.]+$", "", cleaned).strip()
        digest = hashlib.sha256(cleaned.encode()).hexdigest()
        return f"{self._prefix}{digest}"

    def get(self, query: str) -> Optional[dict]:
        if not self._r:
            return None
        key = self._key(query)
        try:
            val = self._r.get(key)
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning("Redis response cache get failed for %s: %s", key, e)
            return None

    def set(self, query: str, payload: dict) -> None:
        if not self._r:
            return
        key = self._key(query)
        try:
            self._r.set(key, json.dumps(payload), ex=self._ttl_seconds)
        except Exception as e:
            logger.warning("Redis response cache set failed for %s: %s", key, e)

_shared: Optional[ResponseCache] = None

def get_response_cache() -> ResponseCache:
    global _shared
    if _shared is None:
        _shared = ResponseCache()
    return _shared

def reset_response_cache_for_tests(cache: Optional[ResponseCache] = None) -> None:
    global _shared
    _shared = cache
