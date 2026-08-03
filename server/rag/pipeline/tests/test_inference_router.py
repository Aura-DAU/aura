"""Unit tests for InferenceRouter concurrency / failover behaviour."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from openai import APIConnectionError

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pipeline.exceptions import RAGPipelineError
from pipeline.inference_router import InferenceRouter


def _conn_err() -> APIConnectionError:
    return APIConnectionError(request=httpx.Request("POST", "http://node-a:8000/v1/chat/completions"))


@pytest.fixture(autouse=True)
def _fresh_router(monkeypatch):
    InferenceRouter._reset_for_tests()
    monkeypatch.setenv(
        "VLLM_ENDPOINTS",
        "http://node-a:8000/v1,http://node-b:8000/v1,http://node-c:8000/v1",
    )
    monkeypatch.setenv("VLLM_MODEL", "test-model")
    # Queue-aware routing is ON in production, but the background poller must
    # never start during unit tests — it would fire real HTTP at node-a/b/c and
    # leak a thread across cases. Tests that exercise selection publish samples
    # straight into the cache; the scrape itself is tested in isolation.
    monkeypatch.setenv("VLLM_QUEUE_AWARE", "0")
    yield
    InferenceRouter._reset_for_tests()
    assert InferenceRouter._queue_thread is None


def _publish(node: str, depth: float, age: float = 0.0) -> None:
    """Seed the queue cache as a successful scrape `age` seconds ago would."""
    with InferenceRouter._lock:
        InferenceRouter._queue_depth[node] = depth
        InferenceRouter._queue_ts[node] = time.monotonic() - age


def _enable_queue_aware(monkeypatch) -> None:
    """Turn on queue-aware scoring without starting the poller thread."""
    InferenceRouter._initialize()
    monkeypatch.setattr(InferenceRouter, "_QUEUE_AWARE", True)
    monkeypatch.setattr(InferenceRouter, "_ensure_queue_thread", classmethod(lambda cls: None))


def test_default_model_matches_live_served_id(monkeypatch):
    monkeypatch.delenv("VLLM_MODEL", raising=False)

    assert InferenceRouter.model_name() == "aura-llm"


def test_pick_node_random_tie_break_spreads_cold_start(monkeypatch):
    # Freeze random.choice to cycle through tied candidates so we can assert
    # the tie-break path is used (not always candidates[0]).
    choices: list[str] = []
    real_choice = __import__("random").choice

    def tracking_choice(seq):
        picked = real_choice(seq)
        choices.append(picked)
        return picked

    monkeypatch.setattr("pipeline.inference_router.random.choice", tracking_choice)

    seen = set()
    for _ in range(30):
        node = InferenceRouter._pick_node()
        seen.add(node)
        InferenceRouter._release_node(node)

    assert len(seen) > 1
    assert all(n.startswith("http://node-") for n in seen)
    assert choices  # tie-break invoked


def test_release_never_goes_negative():
    InferenceRouter._initialize()
    node = InferenceRouter._nodes[0]
    InferenceRouter._release_node(node)  # release without pick
    assert InferenceRouter.stats()[node]["inflight"] == 0


def test_call_with_rotation_releases_inflight_on_success(monkeypatch):
    def ok(client):
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))])

    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(lambda cls, n: object()))
    result = InferenceRouter.call_with_rotation(ok, max_retries=2)
    assert result.choices[0].message.content == "ok"
    assert all(s["inflight"] == 0 for s in InferenceRouter.stats().values())


def test_call_with_rotation_releases_inflight_on_non_sdk_error(monkeypatch):
    def boom(client):
        raise ValueError("bug in fn")

    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(lambda cls, n: object()))
    with pytest.raises(ValueError, match="bug in fn"):
        InferenceRouter.call_with_rotation(boom, max_retries=2)
    assert all(s["inflight"] == 0 for s in InferenceRouter.stats().values())


def test_call_with_rotation_holds_inflight_until_stream_closes(monkeypatch):
    class FakeStream:
        def __init__(self):
            self.closed = False

        def __iter__(self):
            yield "chunk-1"
            yield "chunk-2"

        def close(self):
            self.closed = True

    stream = FakeStream()
    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(lambda cls, n: object()))

    wrapped = InferenceRouter.call_with_rotation(lambda _c: stream, max_retries=2)
    # Slot still held while the stream is open / unread.
    assert sum(s["inflight"] for s in InferenceRouter.stats().values()) == 1

    assert list(wrapped) == ["chunk-1", "chunk-2"]
    assert all(s["inflight"] == 0 for s in InferenceRouter.stats().values())


def test_call_with_rotation_failover_on_connection_error(monkeypatch):
    attempts: list[str] = []

    def flaky(client):
        # _client_for is mocked to return the node url string itself.
        attempts.append(client)
        if len(attempts) < 2:
            raise _conn_err()
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(lambda cls, n: n))
    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, *_a, **_k: 0.0))

    result = InferenceRouter.call_with_rotation(flaky, max_retries=3, initial_retry_delay=0.01)
    assert result.ok is True
    assert len(attempts) == 2
    assert attempts[0] != attempts[1] or len(InferenceRouter._nodes) == 1


def test_call_with_rotation_exhausts_pool(monkeypatch):
    def always_down(client):
        raise _conn_err()

    monkeypatch.setattr(InferenceRouter, "_client_for", classmethod(lambda cls, n: object()))
    monkeypatch.setattr(InferenceRouter, "_backoff_delay", classmethod(lambda cls, *_a, **_k: 0.0))

    with pytest.raises(RAGPipelineError, match="exhausted"):
        InferenceRouter.call_with_rotation(always_down, max_retries=3, initial_retry_delay=0.01)
    assert all(s["inflight"] == 0 for s in InferenceRouter.stats().values())


# ── GPU-07: queue-aware selection ────────────────────────────────────────────

_METRICS_PAGE = """\
# HELP vllm:num_requests_running Number of requests in model execution batches.
# TYPE vllm:num_requests_running gauge
vllm:num_requests_running{engine="0",model_name="aura-llm"} 24.0
# HELP vllm:num_requests_waiting Number of requests waiting to be processed.
# TYPE vllm:num_requests_waiting gauge
vllm:num_requests_waiting{engine="0",model_name="aura-llm"} 72.0
# HELP vllm:num_requests_waiting_by_reason Number of waiting requests by reason.
# TYPE vllm:num_requests_waiting_by_reason gauge
vllm:num_requests_waiting_by_reason{engine="0",model_name="aura-llm",reason="capacity"} 72.0
vllm:num_requests_waiting_by_reason{engine="0",model_name="aura-llm",reason="deferred"} 0.0
# HELP vllm:kv_cache_usage_perc KV-cache usage. 1 means 100 percent usage.
# TYPE vllm:kv_cache_usage_perc gauge
vllm:kv_cache_usage_perc{engine="0",model_name="aura-llm"} 0.0
"""


def test_parse_queue_metrics_matches_live_vllm_payload():
    # 24 running + 72 waiting. The by_reason breakdown sums to the same 72 and
    # must NOT be double counted, and the "# HELP"/"# TYPE" lines must not parse.
    assert InferenceRouter._parse_queue_metrics(_METRICS_PAGE) == 96.0


def test_parse_queue_metrics_adds_kv_pressure_penalty():
    saturated = _METRICS_PAGE.replace(
        'vllm:kv_cache_usage_perc{engine="0",model_name="aura-llm"} 0.0',
        'vllm:kv_cache_usage_perc{engine="0",model_name="aura-llm"} 1.0',
    )
    # 96 outstanding + the full _QUEUE_KV_PENALTY at 100% KV usage.
    assert InferenceRouter._parse_queue_metrics(saturated) == pytest.approx(
        96.0 + InferenceRouter._QUEUE_KV_PENALTY
    )


def test_parse_queue_metrics_returns_none_for_non_vllm_page():
    assert InferenceRouter._parse_queue_metrics("<html>404 not found</html>") is None


def test_metrics_url_is_sibling_of_v1_root():
    assert InferenceRouter._metrics_url("http://node-a:8001/v1") == "http://node-a:8001/metrics"
    assert InferenceRouter._metrics_url("http://node-a:8001/v1/") == "http://node-a:8001/metrics"


def test_pick_node_prefers_shallow_queue_over_deep_one(monkeypatch):
    _enable_queue_aware(monkeypatch)
    a, b, c = InferenceRouter._nodes
    # The GPU-01 measurement: node-a buried, the other two genuinely idle.
    _publish(a, 96.0)
    _publish(b, 0.0)
    _publish(c, 0.0)

    picks = []
    for _ in range(50):
        node = InferenceRouter._pick_node()
        picks.append(node)
        InferenceRouter._release_node(node)

    assert a not in picks
    assert set(picks) == {b, c}


def test_pick_node_queue_signal_overrides_local_inflight(monkeypatch):
    # The cross-worker case that a per-process counter cannot see: this worker
    # has dispatched to node-b and nothing to node-a, so local least-connections
    # would pick node-a — but a sibling worker has already buried it.
    _enable_queue_aware(monkeypatch)
    a, b, _c = InferenceRouter._nodes
    _publish(a, 40.0)
    _publish(b, 3.0)
    with InferenceRouter._lock:
        InferenceRouter._inflight[b] = 3

    assert InferenceRouter._pick_node(exclude={_c}) == b


def test_pick_node_does_not_double_count_local_inflight(monkeypatch):
    # A scrape sees requests this worker already dispatched, so cost is the max
    # of the two lower bounds, not their sum. Streams hold their slot for the
    # whole generation, so summing would penalise a node twice for one request.
    _enable_queue_aware(monkeypatch)
    a, _b, _c = InferenceRouter._nodes
    _publish(a, 5.0)
    with InferenceRouter._lock:
        InferenceRouter._inflight[a] = 5
    now = time.monotonic()
    with InferenceRouter._lock:
        assert InferenceRouter._node_cost(a, now) == 5.0


def test_pick_node_falls_back_to_local_when_sample_is_stale(monkeypatch):
    _enable_queue_aware(monkeypatch)
    a, b, c = InferenceRouter._nodes
    # node-a is deeply queued but the reading predates the staleness window, so
    # it must be ignored rather than trusted or treated as a penalty.
    _publish(a, 96.0, age=InferenceRouter._QUEUE_STALE_AFTER + 1.0)
    _publish(b, 0.0, age=InferenceRouter._QUEUE_STALE_AFTER + 1.0)
    _publish(c, 0.0, age=InferenceRouter._QUEUE_STALE_AFTER + 1.0)

    seen = set()
    for _ in range(50):
        node = InferenceRouter._pick_node()
        seen.add(node)
        InferenceRouter._release_node(node)

    assert seen == {a, b, c}  # plain least-connections + random tie-break


def test_scrape_failure_leaves_cache_untouched_and_fails_open(monkeypatch):
    _enable_queue_aware(monkeypatch)
    a, b, c = InferenceRouter._nodes

    class ExplodingClient:
        def get(self, url):
            raise httpx.ConnectError("metrics endpoint down")

    InferenceRouter._scrape_node(ExplodingClient(), a)

    assert InferenceRouter._queue_ts == {}
    seen = set()
    for _ in range(50):
        node = InferenceRouter._pick_node()
        seen.add(node)
        InferenceRouter._release_node(node)

    assert seen == {a, b, c}


def test_scrape_non_200_does_not_overwrite_a_good_sample(monkeypatch):
    _enable_queue_aware(monkeypatch)
    a = InferenceRouter._nodes[0]
    _publish(a, 96.0)

    class ErrorClient:
        def get(self, url):
            return SimpleNamespace(status_code=503, text="upstream unavailable")

    InferenceRouter._scrape_node(ErrorClient(), a)
    assert InferenceRouter._queue_depth[a] == 96.0


def test_scrape_records_depth_from_metrics_payload(monkeypatch):
    _enable_queue_aware(monkeypatch)
    a = InferenceRouter._nodes[0]
    requested: list[str] = []

    class OkClient:
        def get(self, url):
            requested.append(url)
            return SimpleNamespace(status_code=200, text=_METRICS_PAGE)

    InferenceRouter._scrape_node(OkClient(), a)

    assert requested == ["http://node-a:8000/metrics"]
    assert InferenceRouter._queue_depth[a] == 96.0
    assert InferenceRouter.stats()[a]["queue_depth"] == 96.0


def test_breaker_still_excludes_a_cooling_node_with_an_empty_queue(monkeypatch):
    # A parked node reports queue 0 precisely because it is taking no traffic.
    # Queue depth must never resurrect it ahead of the cooldown.
    _enable_queue_aware(monkeypatch)
    a, b, c = InferenceRouter._nodes
    _publish(a, 0.0)
    _publish(b, 20.0)
    _publish(c, 20.0)
    with InferenceRouter._lock:
        InferenceRouter._cooldown_until[a] = time.monotonic() + 60.0

    picks = {InferenceRouter._pick_node() for _ in range(30)}
    for node in list(picks):
        InferenceRouter._release_node(node)

    assert a not in picks


def test_env_gate_off_restores_plain_least_connections(monkeypatch):
    # Fixture already sets VLLM_QUEUE_AWARE=0; publish a lopsided cache anyway
    # and assert selection ignores it entirely.
    InferenceRouter._initialize()
    assert InferenceRouter._QUEUE_AWARE is False
    a, b, c = InferenceRouter._nodes
    _publish(a, 96.0)
    _publish(b, 0.0)
    _publish(c, 0.0)

    seen = set()
    for _ in range(50):
        node = InferenceRouter._pick_node()
        seen.add(node)
        InferenceRouter._release_node(node)

    assert seen == {a, b, c}
    assert InferenceRouter._queue_thread is None


def test_queue_thread_starts_once_and_is_stopped_by_reset(monkeypatch):
    monkeypatch.setenv("VLLM_QUEUE_AWARE", "1")
    InferenceRouter._reset_for_tests()
    scraped: list[str] = []
    monkeypatch.setattr(
        InferenceRouter,
        "_scrape_node",
        classmethod(lambda cls, client, node: scraped.append(node)),
    )

    first = InferenceRouter._pick_node()
    InferenceRouter._release_node(first)
    thread = InferenceRouter._queue_thread
    assert thread is not None and thread.daemon

    InferenceRouter._pick_node()
    assert InferenceRouter._queue_thread is thread  # not restarted per request

    InferenceRouter._reset_for_tests()
    assert InferenceRouter._queue_thread is None
    thread.join(timeout=3.0)
    assert not thread.is_alive()
