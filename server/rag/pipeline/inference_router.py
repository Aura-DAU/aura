# Inference-Router for the Aura GPU cluster.
#
# Client-side load balancer + failover sitting in front of the vLLM inference
# pool (architecture doc §13 "Inference Router", §14 "LLM Inference Servers").
# It selects the least-loaded *healthy* node, reuses one keep-alive connection
# pool per node, fails fast off dead nodes, and hides the physical topology
# from LangGraph — so scaling to a 4th/5th node is a VLLM_ENDPOINTS edit, not
# an orchestration change (doc §"Scalability of the Architecture").

import os
import re
import time
import random
import threading

import httpx
from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError
from pipeline.exceptions import RAGPipelineError


def _env_float(name: str, default: float) -> float:
    try:
        return float((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    val = (os.getenv(name) or "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


class InferenceRouter:
    # ── Topology / model (immutable once initialized) ────────────────────────
    _nodes: list[str] = []
    _model: str = ""

    # ── Per-node runtime state (all mutations guarded by _lock) ──────────────
    _clients: dict[str, OpenAI] = {}        # pooled keep-alive client per node
    _inflight: dict[str, int] = {}          # active requests → "least connections"
    _fail_streak: dict[str, int] = {}       # consecutive health failures per node
    _cooldown_until: dict[str, float] = {}  # circuit-breaker: node parked until t

    _initialized = False
    _lock = threading.Lock()

    # Fail-fast timeouts. A black-holed node (accepts the TCP connection, then
    # never answers) must trip failover inside the doc's 2–4s budget, not hang
    # a pooled worker thread for the openai SDK's 600s default. The read
    # timeout stays generous for long generations and inter-token gaps on
    # streams; only *connect* is aggressive, since a healthy LAN node connects
    # in single-digit milliseconds.
    _CONNECT_TIMEOUT = _env_float("VLLM_CONNECT_TIMEOUT", 5.0)
    _READ_TIMEOUT = _env_float("VLLM_READ_TIMEOUT", 60.0)

    # Keep-alive pool sized to the doc's ~25 concurrent requests/GPU so
    # steady-state traffic reuses sockets instead of re-handshaking TLS.
    _MAX_KEEPALIVE = _env_int("VLLM_MAX_KEEPALIVE", 32)
    _MAX_CONNECTIONS = _env_int("VLLM_MAX_CONNECTIONS", 128)

    # Circuit breaker. After this many *consecutive* health failures a node is
    # parked (removed from rotation) for a cooldown that grows with the streak,
    # capped. Without it a dead node — having 0 in-flight — looks "least loaded"
    # and is picked FIRST, so every request pays a full failover round-trip.
    _BREAKER_THRESHOLD = _env_int("VLLM_BREAKER_THRESHOLD", 2)
    _COOLDOWN_BASE = _env_float("VLLM_BREAKER_COOLDOWN", 5.0)
    _COOLDOWN_MAX = _env_float("VLLM_BREAKER_COOLDOWN_MAX", 60.0)

    _RETRYABLE_STATUS = (429, 500, 502, 503, 504)
    # 429 means "up but busy" (vLLM burst limit) — a load signal, not ill
    # health — so it never trips the breaker; only these do.
    _HEALTH_FAIL_STATUS = (500, 502, 503, 504)

    @classmethod
    def _initialize(cls):
        # Double-checked locking: the fast path skips the mutex once warm.
        # Safe under CPython's GIL because `_initialized` is written LAST, after
        # every state dict is populated, so no thread can observe it True while
        # the dicts are half-built. (A free-threaded build would need a real
        # barrier here.)
        if cls._initialized:
            return
        with cls._lock:
            if cls._initialized:
                return
            # VLLM_ENDPOINTS: comma-separated base URLs, one per inference node
            # (e.g. "http://vllm-node1:8000/v1,http://vllm-node2:8000/v1,
            # http://vllm-node3:8000/v1"), matching the doc's 3x RTX-4090 pool.
            # VLLM_ENDPOINT (singular) is a single-node convenience alias.
            raw = os.getenv("VLLM_ENDPOINTS") or os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1")
            cls._nodes = [n.strip().rstrip("/") for n in raw.split(",") if n.strip()]
            cls._clients = {}
            cls._inflight = {n: 0 for n in cls._nodes}
            cls._fail_streak = {n: 0 for n in cls._nodes}
            cls._cooldown_until = {n: 0.0 for n in cls._nodes}
            cls._model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-32B-AWQ")
            cls._initialized = True
            print(f"[InferenceRouter] Initialized with {len(cls._nodes)} vLLM node(s): {cls._nodes} (model={cls._model})")

    @classmethod
    def model_name(cls, env_var: str | None = None, default: str | None = None) -> str:
        """Resolve the model name for a call site. Most callers should just
        use the shared VLLM_MODEL (one model replicated across the inference
        pool, per the architecture doc) — env_var/default let a specific
        guardrail override with its own env var, mirroring how WellnessGuardrail
        previously read GROQ_WELLNESS_MODEL."""
        cls._initialize()
        if env_var:
            return os.getenv(env_var, default or cls._model)
        return cls._model

    # ── Reasoning-mode control (single source of truth) ──────────────────────
    # Qwen3 and other hybrid-reasoning models emit a <think>…</think> preamble
    # before every answer unless the chat template is told not to. vLLM exposes
    # that switch through `chat_template_kwargs` on the OpenAI-compatible body,
    # so every call site passes `extra_body=` from one of the two helpers below
    # rather than hardcoding the dict. That preamble is hundreds-to-thousands of
    # decode tokens the caller immediately strips — pure latency on a 32B model.

    @staticmethod
    def no_think_extra_body() -> dict:
        """Reasoning ALWAYS off. For structured / short-output calls (guardrails,
        classifier, query rewriter/planner) whose small max_tokens budget leaves
        no room to think and whose output is terse by design — a <think> block
        there is wasted latency and can truncate the real answer before it's
        emitted."""
        return {"chat_template_kwargs": {"enable_thinking": False}}

    @staticmethod
    def answer_extra_body() -> dict:
        """Reasoning control for FINAL answer generation, where thinking is a
        genuine quality/latency trade-off. Defaults to off (fast); set
        AURA_ENABLE_THINKING=true to let the model reason first (slower, can
        improve adherence on tricky negation / false-premise prompts — validate
        with the eval suite before enabling in prod)."""
        if _env_bool("AURA_ENABLE_THINKING", False):
            return {}
        return {"chat_template_kwargs": {"enable_thinking": False}}

    # ── Node selection & accounting ──────────────────────────────────────────
    @classmethod
    def _pick_node(cls, exclude: set[str] | None = None) -> str:
        cls._initialize()
        if not cls._nodes:
            raise RAGPipelineError("No vLLM inference nodes configured (set VLLM_ENDPOINTS).")
        exclude = exclude or set()
        now = time.monotonic()
        with cls._lock:
            healthy = [
                n for n in cls._nodes
                if n not in exclude and cls._cooldown_until.get(n, 0.0) <= now
            ]
            # Degrade gracefully instead of hard-failing: healthy → any
            # not-in-cooldown → any not-excluded → anything. A parked node that
            # resurfaces here is the breaker's implicit half-open probe.
            candidates = (
                healthy
                or [n for n in cls._nodes if cls._cooldown_until.get(n, 0.0) <= now]
                or [n for n in cls._nodes if n not in exclude]
                or list(cls._nodes)
            )
            # Least-connections: fewest in-flight wins; node order breaks ties
            # deterministically. O(n) over the handful of nodes the doc describes.
            chosen = min(candidates, key=lambda n: cls._inflight.get(n, 0))
            cls._inflight[chosen] = cls._inflight.get(chosen, 0) + 1
            return chosen

    @classmethod
    def _release_node(cls, node: str):
        with cls._lock:
            if node in cls._inflight:
                cls._inflight[node] = max(0, cls._inflight[node] - 1)

    @classmethod
    def _mark_success(cls, node: str):
        with cls._lock:
            cls._fail_streak[node] = 0
            cls._cooldown_until[node] = 0.0

    @classmethod
    def _mark_health_failure(cls, node: str):
        # Trip the breaker after _BREAKER_THRESHOLD consecutive health failures;
        # cooldown grows exponentially with the streak (capped) so a persistently
        # dead node is parked longer while a one-off blip recovers on its next turn.
        with cls._lock:
            streak = cls._fail_streak.get(node, 0) + 1
            cls._fail_streak[node] = streak
            if streak >= cls._BREAKER_THRESHOLD:
                backoff = cls._COOLDOWN_BASE * (2 ** (streak - cls._BREAKER_THRESHOLD))
                cls._cooldown_until[node] = time.monotonic() + min(backoff, cls._COOLDOWN_MAX)

    @staticmethod
    def _record_dispatch(node: str):
        """Best-effort Prometheus counter increment (architecture doc's
        aura-prometheus service). Wrapped in try/except so the pipeline package
        stays importable where `api.metrics` isn't on sys.path yet (e.g.
        standalone pipeline unit tests)."""
        try:
            from api.metrics import INFERENCE_NODE_REQUESTS
            INFERENCE_NODE_REQUESTS.labels(node=node).inc()
        except Exception:
            pass

    @staticmethod
    def _record_failure(node: str):
        try:
            from api.metrics import INFERENCE_NODE_FAILURES
            INFERENCE_NODE_FAILURES.labels(node=node).inc()
        except Exception:
            pass

    # ── Client pooling ───────────────────────────────────────────────────────
    @classmethod
    def _client_for(cls, node: str) -> OpenAI:
        """One pooled client per node, created lazily and reused for the process
        lifetime. A fresh OpenAI() per call rebuilds an httpx connection pool and
        pays a TCP+TLS handshake on every generation. openai/httpx clients are
        thread-safe, so a single instance is shared across worker threads."""
        client = cls._clients.get(node)
        if client is not None:
            return client
        with cls._lock:
            client = cls._clients.get(node)
            if client is None:
                http_client = httpx.Client(
                    timeout=httpx.Timeout(cls._READ_TIMEOUT, connect=cls._CONNECT_TIMEOUT),
                    limits=httpx.Limits(
                        max_connections=cls._MAX_CONNECTIONS,
                        max_keepalive_connections=cls._MAX_KEEPALIVE,
                    ),
                )
                client = OpenAI(
                    base_url=node,
                    api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
                    # We own retry/failover across the pool. The SDK's own 2
                    # silent retries would just re-hammer the SAME (possibly
                    # dead) node and stack latency before our failover runs.
                    max_retries=0,
                    http_client=http_client,
                )
                cls._clients[node] = client
            return client

    @classmethod
    def get_client(cls) -> OpenAI:
        """Borrow the pooled client of the currently least-loaded node, for
        callers (guardrails/classifiers) that hold a client for their object's
        lifetime rather than routing per request. It's a borrow, not an
        in-flight request, so the count is released immediately."""
        node = cls._pick_node()
        cls._release_node(node)
        return cls._client_for(node)

    # ── Retry / failover backoff ─────────────────────────────────────────────
    @classmethod
    def _backoff_delay(cls, base_delay: float, error_msg: str) -> float:
        # Honour an explicit "try again in Xs" hint when vLLM/openai gives one;
        # otherwise use exponential base with EQUAL JITTER (half fixed + half
        # random). Jitter de-syncs a fleet of requests that all failed at once,
        # avoiding a retry thundering-herd back onto the recovering node.
        match = re.search(r"try again in (\d+(?:\.\d+)?)s", error_msg.lower())
        if match:
            return min(float(match.group(1)) + 1.0, 30.0)
        capped = min(base_delay, 30.0)
        return capped / 2.0 + random.uniform(0.0, capped / 2.0)

    @classmethod
    def call_with_rotation(cls, fn, max_retries=5, initial_retry_delay=2.0):
        """Run fn(client) against the least-loaded healthy vLLM node, failing
        over to another node on a retryable error (429/500/502/503/504 or a
        connection error) with jittered exponential backoff. Connection/5xx
        failures trip the failing node's circuit breaker; a 429 is treated as
        transient load, not ill health. Raises RAGPipelineError once the retry
        budget is spent across the pool.

        NOTE: fn should CREATE the request (return a response or an open
        stream). A failure that occurs mid-stream, after the first token, can
        NOT be retried on another node — the caller has already emitted output."""
        cls._initialize()

        tried: set[str] = set()
        retry_delay = initial_retry_delay
        pending_delay = 0.0
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            # Sleep from the *previous* failure happens here, after that node's
            # in-flight slot was already released by the finally below — never
            # while we still hold it.
            if pending_delay:
                time.sleep(pending_delay)
                pending_delay = 0.0

            node = cls._pick_node(exclude=tried if len(tried) < len(cls._nodes) else None)
            try:
                result = fn(cls._client_for(node))
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                last_exc = e
                tried.add(node)
                status_code = getattr(e, "status_code", None)
                is_conn = isinstance(e, APIConnectionError)

                cls._record_failure(node)
                if is_conn or status_code in cls._HEALTH_FAIL_STATUS:
                    cls._mark_health_failure(node)

                if not (is_conn or status_code in cls._RETRYABLE_STATUS):
                    raise RAGPipelineError(
                        f"Inference request failed with unretryable status {status_code}: {e}"
                    ) from e

                if attempt < max_retries - 1:
                    pending_delay = cls._backoff_delay(retry_delay, str(e))
                    retry_delay *= 2
                    print(f"[InferenceRouter] Node {node} error {status_code}: {e}. "
                          f"Failing over in {pending_delay:.1f}s (attempt {attempt + 1}/{max_retries})...")
            except Exception:
                # Non-SDK error (a bug in fn, a malformed response). Not a node
                # health signal, but the finally still releases the in-flight
                # slot — otherwise the counter leaks and this node looks
                # permanently "least loaded" and gets over-selected forever.
                cls._record_failure(node)
                raise
            else:
                cls._mark_success(node)
                cls._record_dispatch(node)
                return result
            finally:
                cls._release_node(node)

        raise RAGPipelineError(
            f"All vLLM inference nodes exhausted after {max_retries} attempts: {last_exc}"
        ) from last_exc

    # ── Introspection (ops/debug/tests; cheap point-in-time snapshot) ────────
    @classmethod
    def stats(cls) -> dict[str, dict]:
        cls._initialize()
        now = time.monotonic()
        with cls._lock:
            return {
                n: {
                    "inflight": cls._inflight.get(n, 0),
                    "fail_streak": cls._fail_streak.get(n, 0),
                    "cooling_down": cls._cooldown_until.get(n, 0.0) > now,
                }
                for n in cls._nodes
            }
