# InferenceRouter

import os
import re
import time
import threading

from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError
from pipeline.exceptions import RAGPipelineError


class InferenceRouter:
    _nodes: list[str] = []
    _inflight: dict[str, int] = {}
    _model: str = ""
    _initialized = False
    _lock = threading.Lock()

    @classmethod
    def _initialize(cls):
        with cls._lock:
            if cls._initialized:
                return

            # VLLM_ENDPOINTS: comma-separated base URLs, one per inference
            # node (e.g. "http://vllm-node1:8000/v1,http://vllm-node2:8000/v1,
            # http://vllm-node3:8000/v1"), matching the architecture doc's
            # 3x RTX-4090 inference pool. VLLM_ENDPOINT (singular) is kept as
            # a single-node convenience alias.
            raw = os.getenv("VLLM_ENDPOINTS") or os.getenv("VLLM_ENDPOINT", "http://localhost:8000/v1")
            cls._nodes = [n.strip().rstrip("/") for n in raw.split(",") if n.strip()]
            cls._inflight = {n: 0 for n in cls._nodes}
            cls._model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-32B-AWQ")
            cls._initialized = True
            print(f"[InferenceRouter] Initialized with {len(cls._nodes)} vLLM node(s): {cls._nodes} (model={cls._model})")

    @classmethod
    def model_name(cls, env_var: str | None = None, default: str | None = None) -> str:
        """Resolve the model name for a call site. Most callers should just
        use the shared VLLM_MODEL (one model replicated across the
        inference pool, per the architecture doc) — env_var/default let a
        specific guardrail override with its own env var, mirroring how
        WellnessGuardrail previously read GROQ_WELLNESS_MODEL."""
        cls._initialize()
        if env_var:
            return os.getenv(env_var, default or cls._model)
        return cls._model

    @classmethod
    def _pick_node(cls, exclude: set[str] | None = None) -> str:
        cls._initialize()
        if not cls._nodes:
            raise RAGPipelineError("No vLLM inference nodes configured (set VLLM_ENDPOINTS).")
        exclude = exclude or set()
        with cls._lock:
            candidates = [n for n in cls._nodes if n not in exclude] or list(cls._nodes)
            candidates.sort(key=lambda n: cls._inflight.get(n, 0))
            chosen = candidates[0]
            cls._inflight[chosen] = cls._inflight.get(chosen, 0) + 1
            return chosen

    @classmethod
    def _release_node(cls, node: str):
        with cls._lock:
            if node in cls._inflight:
                cls._inflight[node] = max(0, cls._inflight[node] - 1)

    @staticmethod
    def _record_dispatch(node: str):
        """Best-effort Prometheus counter increment (architecture doc's
        aura-prometheus service). Wrapped in try/except so the pipeline
        package stays importable in contexts where `api.metrics` isn't on
        sys.path yet (e.g. standalone pipeline unit tests)."""
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

    @classmethod
    def _make_client(cls, node: str) -> OpenAI:
        return OpenAI(base_url=node, api_key=os.getenv("VLLM_API_KEY", "EMPTY"))

    @classmethod
    def get_client(cls) -> OpenAI:
        """A client bound to the currently least-loaded node, for callers
        that keep a client around for their object's lifetime rather than
        routing per-request."""
        node = cls._pick_node()
        cls._release_node(node)  # this is a borrow, not an in-flight request
        return cls._make_client(node)

    @classmethod
    def call_with_rotation(cls, fn, max_retries=5, initial_retry_delay=2.0):
        """Executes fn(client) against the least-loaded vLLM node.
        On a retryable error (429/500/502/503/504, connection errors), picks
        a different node and retries with exponential backoff. Raises
        RAGPipelineError once every node has been tried without success."""
        cls._initialize()

        tried: set[str] = set()
        retry_delay = initial_retry_delay
        attempt = 0

        node = cls._pick_node()
        client = cls._make_client(node)

        while attempt < max_retries:
            try:
                result = fn(client)
                cls._release_node(node)
                cls._record_dispatch(node)
                return result
            except (RateLimitError, APIStatusError, APIConnectionError) as e:
                cls._release_node(node)
                cls._record_failure(node)
                tried.add(node)
                status_code = getattr(e, "status_code", None)
                error_msg = str(e).lower()

                is_retryable = (status_code in (429, 500, 502, 503, 504)) or isinstance(e, APIConnectionError)
                if not is_retryable:
                    raise RAGPipelineError(f"Inference request failed with unretryable status {status_code}: {e}") from e

                if len(tried) >= len(cls._nodes) and attempt == max_retries - 1:
                    raise RAGPipelineError(f"All vLLM inference nodes exhausted: {e}") from e

                retry_after = retry_delay
                match = re.search(r"try again in (\d+(?:\.\d+)?)s", error_msg)
                if match:
                    retry_after = float(match.group(1)) + 1.0
                retry_after = min(retry_after, 30.0)

                print(f"[InferenceRouter] Node {node} error {status_code}: {e}. Routing to next node in {retry_after:.1f}s...")
                time.sleep(retry_after)
                retry_delay *= 2
                attempt += 1

                exclude = tried if len(tried) < len(cls._nodes) else None
                node = cls._pick_node(exclude=exclude)
                client = cls._make_client(node)

        raise RAGPipelineError("Max retries exceeded across all vLLM inference nodes.")
