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

from prometheus_client import (
    Counter,
    Histogram,
    CONTENT_TYPE_LATEST,
    generate_latest,
)

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


def metrics_response():
    """Return (body_bytes, content_type) for the /metrics endpoint."""
    return generate_latest(), CONTENT_TYPE_LATEST
