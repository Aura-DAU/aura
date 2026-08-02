import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure imports work from server root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# `redis` is a declared dependency (server/requirements.txt) and every test here
# patches Redis.from_url, so no client is ever constructed. Do NOT swap
# sys.modules['redis'] for a mock: that leaks for the rest of the session and
# makes redis exception types unmatchable in every later test — it silently
# broke the WatchError retry assertions in test_user_memory.py.
import pytest
from pipeline.memory.response_cache import (
    ResponseCache,
    get_response_cache,
    reset_response_cache_for_tests,
)

def test_response_cache_normalizes_and_hashes_keys():
    client = MagicMock()
    with patch("redis.Redis.from_url", return_value=client):
        cache = ResponseCache()
        cache.redis_url = "redis://localhost:6379/0"
        cache._r = client
        
        # Norm case-insensitivity and spacing
        k1 = cache._key("What is the B.Tech ICT Fee?")
        k2 = cache._key("  what  is  the  b.tech  ict  fee?  ")
        assert k1 == k2
        
        assert k1.startswith("aura:public-cache:")
        assert len(k1) == len("aura:public-cache:") + 64

def test_response_cache_get_hit_and_miss():
    client = MagicMock()
    client.get.return_value = '{"answer": "A1", "sources": ["S1"]}'
    with patch("redis.Redis.from_url", return_value=client):
        cache = ResponseCache()
        cache.redis_url = "redis://localhost:6379/0"
        cache._r = client
        
        res = cache.get("test query")
        assert res == {"answer": "A1", "sources": ["S1"]}
        client.get.assert_called_once()
        
        client.get.return_value = None
        res_miss = cache.get("other query")
        assert res_miss is None

def test_response_cache_set():
    client = MagicMock()
    with patch("redis.Redis.from_url", return_value=client):
        cache = ResponseCache()
        cache.redis_url = "redis://localhost:6379/0"
        cache._r = client
        
        payload = {"answer": "A2", "sources": []}
        cache.set("test query", payload)
        client.set.assert_called_once()
        args, kwargs = client.set.call_args
        assert kwargs.get("ex") == 86400

def test_response_cache_fails_gracefully_when_redis_is_down():
    client = MagicMock()
    client.get.side_effect = Exception("Redis is down")
    client.set.side_effect = Exception("Redis is down")
    with patch("redis.Redis.from_url", return_value=client):
        cache = ResponseCache()
        cache.redis_url = "redis://localhost:6379/0"
        cache._r = client
        
        # Should gracefully return None on failures
        assert cache.get("test query") is None
        
        # Should gracefully return without crashing
        try:
            cache.set("test query", {"answer": "A"})
        except Exception:
            pytest.fail("set() raised an error when Redis was down")
