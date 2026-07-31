from __future__ import annotations
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
    #
    # 120s, not 60s: a node saturated at its measured knee (~780 generated
    # tok/s, max_num_seqs=24) serving a full admission wave of 96 requests at
    # ~512 output tokens each needs ~63s of wall clock before the last one
    # finishes. A 60s read timeout cuts those off mid-queue and converts a
    # merely-slow node into a failover storm. Both env examples already say 120.
    _CONNECT_TIMEOUT = _env_float("VLLM_CONNECT_TIMEOUT", 5.0)
    _READ_TIMEOUT = _env_float("VLLM_READ_TIMEOUT", 120.0)

    # Keep-alive pool sized for bursty admission (many short classifier calls
    # plus a smaller number of long generations). Under a 1000-user spike the
    # per-process httpx pool must not collapse to connect thrash; size to the
    # higher of (CHAT_CONCURRENCY × LLM-calls-per-ask) and vLLM's real
    # concurrent-sequence capacity. Override via env on multi-replica hosts.
    _MAX_KEEPALIVE = _env_int("VLLM_MAX_KEEPALIVE", 64)
    _MAX_CONNECTIONS = _env_int("VLLM_MAX_CONNECTIONS", 256)

    # Throttle failover prints so a pool outage under load doesn't flood logs.
    _FAILOVER_LOG_INTERVAL = _env_float("VLLM_FAILOVER_LOG_INTERVAL", 5.0)
    _last_failover_log: dict[str, float] = {}

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

    # ── Queue-aware selection: the cross-worker load signal ──────────────────
    # `_inflight` only knows what THIS uvicorn worker dispatched. With N workers
    # per replica each one independently believes the pool is idle, so
    # least-connections degenerates into N uncoordinated random walks: a node
    # can sit at running=24/waiting=80 while a worker that hasn't sent it much
    # still rates it free. vLLM publishes the truth on its own /metrics, so a
    # background thread polls that and selection reads the cached value.
    #
    # Strictly advisory, and never on the request path. A node with no fresh
    # sample falls back to its local in-flight count, so a metrics outage
    # degrades routing to exactly the previous behaviour instead of taking
    # inference down. Set VLLM_QUEUE_AWARE=0 to disable without a code change.
    _QUEUE_AWARE = _env_bool("VLLM_QUEUE_AWARE", True)
    _QUEUE_SCRAPE_INTERVAL = _env_float("VLLM_QUEUE_SCRAPE_INTERVAL", 2.0)
    # Discard a sample older than this. Default is 3 scrape intervals, so one
    # missed poll doesn't flip the router back to local-only.
    _QUEUE_STALE_AFTER = _env_float("VLLM_QUEUE_STALE_AFTER", 6.0)
    _QUEUE_SCRAPE_TIMEOUT = _env_float("VLLM_QUEUE_SCRAPE_TIMEOUT", 1.0)

    # KV-cache pressure, folded into the same sample. Request counts alone
    # under-describe these nodes: measured KV is only 23,856 tokens
    # (kv_cache_max_concurrency=2.91 at max_model_len=8192), so 8 concurrent
    # ~5k-token RAG prompts reach 92% KV and drive short-query p95 from 1.9s to
    # 25s while `running` is still well under the max_num_seqs=24 ceiling. A
    # node that looks cheap by request count can already be thrashing. Above the
    # soft threshold we add up to _QUEUE_KV_PENALTY phantom requests, scaled
    # linearly — 8 because that is the concurrency that saturated KV in
    # measurement. Set the penalty to 0 to score on request counts alone.
    _QUEUE_KV_SOFT = _env_float("VLLM_QUEUE_KV_SOFT", 0.85)
    _QUEUE_KV_PENALTY = _env_float("VLLM_QUEUE_KV_PENALTY", 8.0)

    _queue_depth: dict[str, float] = {}   # last observed load estimate per node
    _queue_ts: dict[str, float] = {}      # monotonic time of that observation
    _queue_thread: threading.Thread | None = None
    _queue_stop: threading.Event | None = None

    # Anchored with re.M so the "# HELP"/"# TYPE" comment lines are skipped, and
    # so `vllm:num_requests_waiting_by_reason` — a per-reason breakdown whose
    # reasons sum to num_requests_waiting — is not counted a second time.
    _RUNNING_RE = re.compile(r"^vllm:num_requests_running(?:\{[^}]*\})?\s+(\S+)\s*$", re.M)
    _WAITING_RE = re.compile(r"^vllm:num_requests_waiting(?:\{[^}]*\})?\s+(\S+)\s*$", re.M)
    _KV_USAGE_RE = re.compile(r"^vllm:kv_cache_usage_perc(?:\{[^}]*\})?\s+(\S+)\s*$", re.M)

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
            cls._queue_depth = {}
            cls._queue_ts = {}
            # Re-read the queue knobs here rather than trusting the values
            # captured at import: the process often loads its .env afterwards.
            cls._QUEUE_AWARE = _env_bool("VLLM_QUEUE_AWARE", True)
            cls._QUEUE_SCRAPE_INTERVAL = _env_float("VLLM_QUEUE_SCRAPE_INTERVAL", 2.0)
            cls._QUEUE_STALE_AFTER = _env_float("VLLM_QUEUE_STALE_AFTER", 6.0)
            cls._QUEUE_SCRAPE_TIMEOUT = _env_float("VLLM_QUEUE_SCRAPE_TIMEOUT", 1.0)
            cls._QUEUE_KV_SOFT = _env_float("VLLM_QUEUE_KV_SOFT", 0.85)
            cls._QUEUE_KV_PENALTY = _env_float("VLLM_QUEUE_KV_PENALTY", 8.0)
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
    #
    # IMPORTANT: `chat_template_kwargs` is a vLLM-only extension. Hosted APIs
    # like Groq reject it with HTTP 400. The helpers below return {} when the
    # configured endpoint is not a local vLLM instance so that the same code
    # path works whether we're pointed at a GPU cluster or Groq fallback.

    @classmethod
    def _is_vllm(cls) -> bool:
        """Return True only when the first configured endpoint looks like a
        local/private vLLM server (not groq.com, openai.com, or similar)."""
        cls._initialize()
        if not cls._nodes:
            return False
        first = cls._nodes[0].lower()
        # Hosted APIs that do NOT support chat_template_kwargs
        hosted = ("groq.com", "openai.com", "anthropic.com", "together.ai",
                  "fireworks.ai", "mistral.ai", "cohere.com")
        return not any(h in first for h in hosted)

    @classmethod
    def no_think_extra_body(cls) -> dict:
        """Reasoning ALWAYS off. For structured / short-output calls (guardrails,
        classifier, query rewriter/planner) whose small max_tokens budget leaves
        no room to think and whose output is terse by design — a <think> block
        there is wasted latency and can truncate the real answer before it's
        emitted. Returns {} for hosted APIs that don't support this extension."""
        if not cls._is_vllm():
            return {}
        return {"chat_template_kwargs": {"enable_thinking": False}}

    @classmethod
    def answer_extra_body(cls) -> dict:
        """Reasoning control for FINAL answer generation, where thinking is a
        genuine quality/latency trade-off. Defaults to off (fast); set
        AURA_ENABLE_THINKING=true to let the model reason first (slower, can
        improve adherence on tricky negation / false-premise prompts — validate
        with the eval suite before enabling in prod). Returns {} for hosted APIs
        that don't support this extension."""
        if not cls._is_vllm():
            return {}
        if _env_bool("AURA_ENABLE_THINKING", False):
            return {}
        return {"chat_template_kwargs": {"enable_thinking": False}}

    # ── Queue scraping (background only — never on the request path) ─────────
    @staticmethod
    def _metrics_url(node: str) -> str:
        """vLLM serves Prometheus text at /metrics, a sibling of the /v1 root."""
        base = node.rstrip("/")
        if base.endswith("/v1"):
            base = base[: -len("/v1")]
        return f"{base}/metrics"

    @staticmethod
    def _sum_metric(pattern: re.Pattern[str], payload: str) -> tuple[float, bool]:
        """Sum every sample of one metric. Data-parallel vLLM emits one series
        per engine, so a single node can legitimately return several lines."""
        total = 0.0
        found = False
        for raw in pattern.findall(payload):
            try:
                total += float(raw)
            except (TypeError, ValueError):
                continue
            found = True
        return total, found

    @classmethod
    def _parse_queue_metrics(cls, payload: str) -> float | None:
        """Turn a /metrics page into one load estimate, in units of requests.

        Returns None when the page carries no vLLM queue gauges at all — a
        proxy error page or a non-vLLM endpoint — so the caller leaves the
        previous sample to age out rather than recording a bogus zero."""
        running, saw_running = cls._sum_metric(cls._RUNNING_RE, payload)
        waiting, saw_waiting = cls._sum_metric(cls._WAITING_RE, payload)
        if not (saw_running or saw_waiting):
            return None
        depth = running + waiting
        usage, saw_kv = cls._sum_metric(cls._KV_USAGE_RE, payload)
        if saw_kv and cls._QUEUE_KV_PENALTY > 0.0:
            soft = cls._QUEUE_KV_SOFT
            if usage > soft:
                depth += cls._QUEUE_KV_PENALTY * (usage - soft) / max(1e-6, 1.0 - soft)
        return depth

    @classmethod
    def _scrape_node(cls, client: httpx.Client, node: str) -> None:
        # Network I/O happens OUTSIDE _lock; the lock is taken only to publish
        # the result, so a hung node can never stall node selection.
        try:
            resp = client.get(cls._metrics_url(node))
            if resp.status_code != 200:
                return
            depth = cls._parse_queue_metrics(resp.text)
        except Exception:
            return  # fail open: the last good sample simply goes stale
        if depth is None:
            return
        with cls._lock:
            cls._queue_depth[node] = depth
            cls._queue_ts[node] = time.monotonic()

    @classmethod
    def _queue_loop(cls, stop: threading.Event) -> None:
        client = httpx.Client(timeout=httpx.Timeout(cls._QUEUE_SCRAPE_TIMEOUT))
        try:
            while not stop.is_set():
                for node in list(cls._nodes):
                    if stop.is_set():
                        break
                    cls._scrape_node(client, node)
                stop.wait(cls._QUEUE_SCRAPE_INTERVAL)
        finally:
            try:
                client.close()
            except Exception:
                pass

    @classmethod
    def _ensure_queue_thread(cls) -> None:
        """Start the poller on first selection, not at import — one-shot
        ingestion and CLI entrypoints import this module without ever routing.

        MUST be called with _lock released."""
        if not cls._QUEUE_AWARE or cls._queue_thread is not None:
            return
        if not cls._is_vllm():
            return  # hosted APIs (Groq et al.) publish no vLLM queue gauges
        with cls._lock:
            if cls._queue_thread is not None:
                return
            stop = threading.Event()
            thread = threading.Thread(
                target=cls._queue_loop,
                args=(stop,),
                name="vllm-queue-scrape",
                daemon=True,
            )
            cls._queue_stop = stop
            cls._queue_thread = thread
        thread.start()

    @classmethod
    def _stop_queue_thread(cls) -> None:
        """MUST be called with _lock released."""
        with cls._lock:
            stop, thread = cls._queue_stop, cls._queue_thread
            cls._queue_stop = None
            cls._queue_thread = None
        if stop is not None:
            stop.set()
        if thread is not None and thread.is_alive():
            thread.join(timeout=3.0)

    # ── Node selection & accounting ──────────────────────────────────────────
    @classmethod
    def _node_cost(cls, node: str, now: float) -> float:
        """Estimated outstanding requests at `node`. Caller must hold _lock.

        The scraped depth already includes whatever this worker dispatched and
        vLLM has admitted, so *adding* the local count would double-count our
        own requests — doubly wrong now that streams hold their in-flight slot
        for the whole generation. Both numbers are lower bounds on true load:
        the scrape sees every worker but lags by up to one interval, the local
        count sees only us but is exact and instant. Taking the max keeps the
        stronger of the two without inventing load that isn't there."""
        local = float(cls._inflight.get(node, 0))
        if not cls._QUEUE_AWARE:
            return local
        ts = cls._queue_ts.get(node)
        if ts is None or (now - ts) > cls._QUEUE_STALE_AFTER:
            return local
        return max(local, cls._queue_depth.get(node, 0.0))

    @classmethod
    def _pick_node(cls, exclude: set[str] | None = None) -> str:
        cls._initialize()
        if not cls._nodes:
            raise RAGPipelineError("No vLLM inference nodes configured (set VLLM_ENDPOINTS).")
        cls._ensure_queue_thread()
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
            # Least-loaded wins, where "load" is the local in-flight count
            # corrected by the node's real vLLM queue when we have a fresh
            # reading. Random tie-break so a cold start (all zeros) or a
            # synchronized release doesn't pin every request onto candidates[0]
            # and create a hotspot. With no usable samples every cost collapses
            # to the local count and this is plain least-connections again.
            costs = {n: cls._node_cost(n, now) for n in candidates}
            min_cost = min(costs.values())
            tied = [n for n in candidates if costs[n] == min_cost]
            chosen = random.choice(tied)
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
        """Borrow the pooled client of the currently least-loaded node.

        Sticky: the returned client is pinned to one node for the caller's
        lifetime. Prefer ``call_with_rotation`` on every hot request path
        (guardrails, classifiers, generators) so failover and least-connections
        apply per call. Kept for rare init-only / test borrow sites."""
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
    def _log_failover(
        cls,
        node: str,
        status_code: int | None,
        err: Exception,
        pending_delay: float,
        attempt: int,
        max_retries: int,
    ) -> None:
        now = time.monotonic()
        with cls._lock:
            last = cls._last_failover_log.get(node, 0.0)
            # Always log the first attempt's failure; throttle repeats per node.
            if attempt > 0 and (now - last) < cls._FAILOVER_LOG_INTERVAL:
                return
            cls._last_failover_log[node] = now
        print(
            f"[InferenceRouter] Node {node} error {status_code}: {err}. "
            f"Failing over in {pending_delay:.1f}s "
            f"(attempt {attempt + 1}/{max_retries})..."
        )

    @staticmethod
    def _is_openai_stream(result: object) -> bool:
        # openai.Stream is iterable + closeable and has no .choices until read.
        # ChatCompletion / similar response objects expose .choices immediately.
        return (
            result is not None
            and hasattr(result, "__iter__")
            and callable(getattr(result, "close", None))
            and not hasattr(result, "choices")
        )

    @classmethod
    def _wrap_stream(cls, stream: object, node: str):
        """Hold the in-flight count until the stream is exhausted or closed.

        ``call_with_rotation`` returns as soon as the stream is *opened*; without
        this wrapper the least-connections counter would drop to 0 for the entire
        generation and every new request would pile onto the same "idle" node."""
        released = False

        def _release_once() -> None:
            nonlocal released
            if not released:
                released = True
                cls._release_node(node)

        class _CountedStream:
            __slots__ = ("_stream",)

            def __init__(self, inner: object):
                self._stream = inner

            def __iter__(self):
                try:
                    yield from self._stream  # type: ignore[misc]
                finally:
                    _release_once()

            def __enter__(self):
                return self

            def __exit__(self, *args):
                self.close()
                return False

            def close(self) -> None:
                try:
                    close = getattr(self._stream, "close", None)
                    if callable(close):
                        close()
                finally:
                    _release_once()

            def __getattr__(self, name: str):
                return getattr(self._stream, name)

        return _CountedStream(stream)

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
        NOT be retried on another node — the caller has already emitted output.
        Open streams keep the in-flight slot until they are exhausted or closed."""
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
            release_now = True
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
                    cls._log_failover(
                        node, status_code, e, pending_delay, attempt, max_retries
                    )
            except Exception:
                # Non-SDK error (a bug in fn, a malformed response). Not a node
                # health signal, but the finally still releases the in-flight
                # slot — otherwise the counter leaks and this node looks
                # permanently overloaded (or, if we under-count, under-selected).
                cls._record_failure(node)
                raise
            else:
                cls._mark_success(node)
                cls._record_dispatch(node)
                if cls._is_openai_stream(result):
                    release_now = False
                    return cls._wrap_stream(result, node)
                return result
            finally:
                if release_now:
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
                    # None when we have never scraped this node, or the scrape
                    # is failing — that is the fail-open path, not an error.
                    "queue_depth": cls._queue_depth.get(n),
                    "queue_age": (
                        None if n not in cls._queue_ts else now - cls._queue_ts[n]
                    ),
                    "cost": cls._node_cost(n, now),
                }
                for n in cls._nodes
            }

    @classmethod
    def _reset_for_tests(cls) -> None:
        """Drop process-local router state. Test-only."""
        # Outside the lock: _stop_queue_thread takes it, and joins a thread that
        # may itself be waiting on it.
        cls._stop_queue_thread()
        with cls._lock:
            for client in cls._clients.values():
                try:
                    client.close()
                except Exception:
                    pass
            cls._nodes = []
            cls._model = ""
            cls._clients = {}
            cls._inflight = {}
            cls._fail_streak = {}
            cls._cooldown_until = {}
            cls._last_failover_log = {}
            cls._queue_depth = {}
            cls._queue_ts = {}
            cls._initialized = False
