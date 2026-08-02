# metrics.py — Prometheus instrumentation for the FastAPI backend.

# The architecture doc's containerization table (§Containerization and Deployment
# Strategy) names `aura-prometheus` and `aura-grafana` as two of AURA's Docker
# services, and the Node 1 hardware diagram lists Prometheus + Grafana as
# running components. Neither existed anywhere in the codebase — no
# `/metrics` endpoint, no `prometheus_client` usage. This module closes that
# gap without changing any existing request-handling code paths:

#   - `REQUEST_COUNT` / `REQUEST_LATENCY`: every HTTP request, labeled by
#     route + method + status, mirroring what NGINX/FastAPI would report.
#   - `STAGE_LATENCY`: reuses the exact segments `pipeline/latency_tracker.py`
#     already collects per /chat request (guardrail_time, retrieval_time,
#     generation_time, total_time) — the same "critical path" breakdown
#     the doc's §Understanding the Critical Path and §Estimating the Cost
#     of a Single Request sections describe — so Grafana can plot the doc's
#     2–4 second end-to-end budget against real traffic.
#   - `INFERENCE_NODE_REQUESTS`: increments per vLLM node chosen by
#     InferenceRouter, so the "least-loaded node" behaviour described in
#     §13 (Inference Router) is visible/auditable rather than opaque.

# `/metrics` is intentionally unauthenticated (Prometheus scrapes it directly,
# container-to-container, and it is never routed through the public NGINX
# edge — see .github/deploy/nginx.conf, which only proxies /api/*, /backend/, and /).

# ── Multiprocess mode (OBS-01) ────────────────────────────────────────────
# Must run before prometheus_client is imported: that import binds
# ValueClass from PROMETHEUS_MULTIPROC_DIR once and for all. See
# api/metrics_multiproc.py for the directory lifecycle and the fallback rules.
from api import metrics_multiproc

MULTIPROC_DIR = metrics_multiproc.bootstrap()

from prometheus_client import (  # noqa: E402 — must follow bootstrap()
    Counter,
    Histogram,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

# Metric-type audit for multiprocess mode. Every metric below is a Counter or a
# Histogram; both aggregate across workers by summing their per-process samples,
# which is the correct semantic for "requests dispatched" and for latency
# buckets, and needs no extra configuration.
#
# No Gauge, Summary, Info or Enum is defined here, and that is deliberate — in
# multiprocess mode a Gauge REQUIRES an explicit `multiprocess_mode` (the
# default, 'all', fans every worker out as its own series with a synthetic `pid`
# label, which is almost never what a dashboard wants). If you add one, choose
# the mode from what the number means: 'livesum' for additive per-worker state
# such as in-flight requests or admission slots in use, 'max'/'min' for
# watermarks, 'liveall' only when per-worker breakdown is genuinely wanted, and
# 'mostrecent' for a value that is process-independent (a config or build stamp).
# test_metrics_multiproc.py fails the build if a gauge lands here without one.
#
# Also note: `process_*` and `python_info` are absent from /metrics whenever
# multiprocess mode is on. They are per-process by nature and prometheus_client
# cannot aggregate them; the dashboards do not reference them.

REQUEST_COUNT = Counter(
    "aura_http_requests_total",
    "Total HTTP requests handled by the FastAPI gateway",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "aura_http_request_duration_seconds",
    "End-to-end HTTP request latency",
    ["method", "path"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 3, 4, 5, 8, 13, 21),
)

# Mirrors pipeline/latency_tracker.py's segments so the doc's critical-path
# stages (guardrail, planner, embedding, qdrant_retrieval, reranker, prompt_assembly,
# inference_router, vllm_generation, streaming, total) are each independently observable.
STAGE_LATENCY = Histogram(
    "aura_chat_stage_duration_seconds",
    "Per-stage latency within the /chat pipeline (guardrail, retrieval, generation)",
    ["stage"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 3, 4, 5, 8),
)

RAG_STAGE_LATENCY = Histogram(
    "aura_rag_stage_duration_seconds",
    "Detailed 11-stage latency within the RAG processing pipeline",
    ["stage"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 8.0, 13.0, 21.0),
)

# One counter per vLLM node, incremented by InferenceRouter on dispatch —
# makes the doc's "least-loaded selection, hides topology from LangGraph"
# behaviour (§13) observable without exposing node identity to the
# orchestrator itself (only to the metrics layer).
INFERENCE_NODE_REQUESTS = Counter(
    "aura_inference_node_requests_total",
    "Requests dispatched to each vLLM inference node by InferenceRouter",
    ["node"],
)

INFERENCE_NODE_FAILURES = Counter(
    "aura_inference_node_failures_total",
    "Failed requests per vLLM inference node (triggers InferenceRouter failover)",
    ["node"],
)


_multiproc_registry = None


def _registry():
    """The aggregating registry, built once and re-read on every collect.

    MultiProcessCollector re-globs the sample directory each time it collects,
    so one long-lived instance always sees newly forked workers.
    """
    global _multiproc_registry
    if _multiproc_registry is None:
        _multiproc_registry = metrics_multiproc.build_registry()
    return _multiproc_registry


def metrics_response():
    """Return (body_bytes, content_type) for the /metrics endpoint."""
    if MULTIPROC_DIR:
        try:
            return generate_latest(_registry()), CONTENT_TYPE_LATEST
        except Exception as exc:
            # A scrape must never 500 the endpoint that operators reach for
            # during an incident — fall back to this worker's own view.
            print(f"[metrics] multiprocess collect failed ({exc}); "
                  "serving this worker's registry only", flush=True)
    return generate_latest(), CONTENT_TYPE_LATEST
