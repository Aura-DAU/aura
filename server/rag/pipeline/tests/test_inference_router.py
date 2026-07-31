# Unit tests for InferenceRouter: least-connections, circuit breaker, failover,
# inflight accounting, and env re-init via reset_for_tests.

from __future__ import annotations

import time
from unittest.mock import MagicMock

import pytest
from openai import APIConnectionError, APIStatusError, RateLimitError

from pipeline.exceptions import RAGPipelineError
from pipeline.inference_router import InferenceRouter


NODES = (
    "http://vllm-a:8000/v1",
    "http://vllm-b:8000/v1",
    "http://vllm-c:8000/v1",
)


@pytest.fixture(autouse=True)
def _fresh_router(monkeypatch):
    monkeypatch.setenv("VLLM_ENDPOINTS", ",".join(NODES))
    monkeypatch.setenv("VLLM_MODEL", "test-model")
    monkeypatch.setenv("VLLM_BREAKER_THRESHOLD", "2")
    monkeypatch.setenv("VLLM_BREAKER_COOLDOWN", "30")
    monkeypatch.setenv("VLLM_BREAKER_COOLDOWN_MAX", "60")
    # Class attrs are captured at import time from env — override for tests.
    monkeypatch.setattr(InferenceRouter, "_BREAKER_THRESHOLD", 2)
    monkeypatch.setattr(InferenceRouter, "_COOLDOWN_BASE", 30.0)
    monkeypatch.setattr(InferenceRouter, "_COOLDOWN_MAX", 60.0)
    InferenceRouter.reset_for_tests()
    yield
    InferenceRouter.reset_for_tests()


def _fake_clients(monkeypatch):
    """Avoid real httpx pools; map each node URL to a distinct MagicMock client."""
    clients = {n: MagicMock(name=f"client[{n}]") for n in NODES}

    def _client_for(cls, node):
        return clients[node]

    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(_client_for))
    return clients


def test_pick_node_prefers_least_inflight():
    InferenceRouter._initialize()
    a = InferenceRouter._pick_node()
    b = InferenceRouter._pick_node()
    c = InferenceRouter._pick_node()
    assert {a, b, c} == set(NODES)
    # All three held; fourth should land on whichever still has the fewest
    # (all at 1 after three picks of distinct nodes → any of them).
    for n in (a, b, c):
        InferenceRouter._release_node(n)
    held = InferenceRouter._pick_node()
    InferenceRouter._inflight[held] = 5
    other = InferenceRouter._pick_node()
    assert other != held
    assert InferenceRouter._inflight[other] == 1


def test_cold_pool_spreads_across_nodes():
    # Random tie-break: with every node at 0 in-flight, repeated picks must not
    # all land on _nodes[0] (the old deterministic bias).
    InferenceRouter._initialize()
    seen: set[str] = set()
    for _ in range(30):
        n = InferenceRouter._pick_node()
        seen.add(n)
        InferenceRouter._release_node(n)
    assert len(seen) >= 2


def test_circuit_breaker_parks_node_after_threshold():
    InferenceRouter._initialize()
    dead = NODES[0]
    InferenceRouter._mark_health_failure(dead)
    assert InferenceRouter.stats()[dead]["cooling_down"] is False
    InferenceRouter._mark_health_failure(dead)
    assert InferenceRouter.stats()[dead]["cooling_down"] is True
    assert InferenceRouter.stats()[dead]["fail_streak"] == 2


def test_pick_skips_cooling_down_node():
    InferenceRouter._initialize()
    dead = NODES[0]
    InferenceRouter._mark_health_failure(dead)
    InferenceRouter._mark_health_failure(dead)
    for _ in range(20):
        n = InferenceRouter._pick_node()
        assert n != dead
        InferenceRouter._release_node(n)


def test_success_clears_breaker():
    InferenceRouter._initialize()
    dead = NODES[0]
    InferenceRouter._mark_health_failure(dead)
    InferenceRouter._mark_health_failure(dead)
    assert InferenceRouter.stats()[dead]["cooling_down"] is True
    InferenceRouter._mark_success(dead)
    assert InferenceRouter.stats()[dead]["cooling_down"] is False
    assert InferenceRouter.stats()[dead]["fail_streak"] == 0


def test_call_with_rotation_failsover_on_connection_error(monkeypatch):
    clients = _fake_clients(monkeypatch)
    dead, live = NODES[0], NODES[1]

    def fn(client):
        if client is clients[dead]:
            raise APIConnectionError(request=MagicMock())
        return "ok"

    # Force first pick to the dead node, then allow normal selection.
    picks = [dead]

    def _pick(cls, exclude=None):
        if picks:
            n = picks.pop(0)
            cls._inflight[n] = cls._inflight.get(n, 0) + 1
            return n
        # Prefer live among remaining.
        exclude = exclude or set()
        candidates = [n for n in NODES if n not in exclude] or list(NODES)
        n = live if live in candidates else candidates[0]
        cls._inflight[n] = cls._inflight.get(n, 0) + 1
        return n

    monkeypatch.setattr(InferenceRouter, "_pick_node", classmethod(_pick))
    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, d, m: 0.0))

    assert InferenceRouter.call_with_rotation(fn, max_retries=3) == "ok"
    assert InferenceRouter.stats()[dead]["fail_streak"] >= 1
    # In-flight must not leak after failover.
    assert all(v == 0 for v in InferenceRouter._inflight.values())


def test_call_with_rotation_429_does_not_trip_breaker(monkeypatch):
    clients = _fake_clients(monkeypatch)
    busy = NODES[0]

    calls = {"n": 0}

    def fn(client):
        calls["n"] += 1
        if calls["n"] == 1:
            err = RateLimitError(
                message="Rate limit exceeded — try again in 0.1s",
                response=MagicMock(status_code=429),
                body=None,
            )
            err.status_code = 429
            raise err
        return "ok"

    def _pick(cls, exclude=None):
        # Always hand out `busy` first, then another node.
        exclude = exclude or set()
        n = busy if busy not in exclude else next(x for x in NODES if x not in exclude)
        cls._inflight[n] = cls._inflight.get(n, 0) + 1
        return n

    monkeypatch.setattr(InferenceRouter, "_pick_node", classmethod(_pick))
    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, d, m: 0.0))

    assert InferenceRouter.call_with_rotation(fn, max_retries=3) == "ok"
    assert InferenceRouter.stats()[busy]["fail_streak"] == 0
    assert InferenceRouter.stats()[busy]["cooling_down"] is False


def test_call_with_rotation_unretryable_4xx_raises(monkeypatch):
    _fake_clients(monkeypatch)

    def fn(client):
        err = APIStatusError(
            message="bad request",
            response=MagicMock(status_code=400),
            body=None,
        )
        err.status_code = 400
        raise err

    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, d, m: 0.0))
    with pytest.raises(RAGPipelineError, match="unretryable"):
        InferenceRouter.call_with_rotation(fn, max_retries=3)
    assert all(v == 0 for v in InferenceRouter._inflight.values())


def test_inflight_released_on_non_sdk_exception(monkeypatch):
    _fake_clients(monkeypatch)

    def fn(client):
        raise ValueError("bug in caller")

    with pytest.raises(ValueError, match="bug in caller"):
        InferenceRouter.call_with_rotation(fn, max_retries=3)
    assert all(v == 0 for v in InferenceRouter._inflight.values())


def test_exhausted_retries_raise(monkeypatch):
    _fake_clients(monkeypatch)

    def fn(client):
        raise APIConnectionError(request=MagicMock())

    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, d, m: 0.0))
    with pytest.raises(RAGPipelineError, match="exhausted"):
        InferenceRouter.call_with_rotation(fn, max_retries=2)


def test_reset_for_tests_rereads_env(monkeypatch):
    InferenceRouter._initialize()
    assert len(InferenceRouter._nodes) == 3
    monkeypatch.setenv("VLLM_ENDPOINTS", "http://only-one:8000/v1")
    InferenceRouter.reset_for_tests()
    InferenceRouter._initialize()
    assert InferenceRouter._nodes == ["http://only-one:8000/v1"]


def test_no_think_extra_body_empty_for_hosted(monkeypatch):
    monkeypatch.setenv("VLLM_ENDPOINTS", "https://api.groq.com/openai/v1")
    InferenceRouter.reset_for_tests()
    assert InferenceRouter.no_think_extra_body() == {}
    assert InferenceRouter.answer_extra_body() == {}


def test_no_think_extra_body_for_vllm():
    body = InferenceRouter.no_think_extra_body()
    assert body == {"chat_template_kwargs": {"enable_thinking": False}}
