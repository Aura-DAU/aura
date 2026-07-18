"""
Inference Router — abstracts multiple LLM backends behind a single endpoint.

Architecture PDF Section 13: "The Inference Router is responsible for selecting
the least-loaded inference server, retrying failed requests, and hiding the
physical topology from the orchestration layer."

Current state: the codebase uses Groq's hosted API via KeyManager key-rotation
(pipeline/key_manager.py). This module provides the abstraction layer so that
switching to self-hosted vLLM nodes (the PDF's target) requires only adding
VLLM_ENDPOINT_* env vars — no changes to aura_chat.py or answer_generator.py.

Usage
-----
The module is consumed by answer_generator.py via KeyManager. To activate vLLM
nodes instead of Groq, set the following env vars:

    VLLM_ENDPOINT_1=http://node1:8001/v1
    VLLM_ENDPOINT_2=http://node2:8001/v1
    VLLM_ENDPOINT_3=http://node3:8001/v1

If none are set, the router falls back to the existing Groq key rotation.
"""
from __future__ import annotations

import os
import time
import logging
import threading
from dataclasses import dataclass, field
from typing import Callable, Any

logger = logging.getLogger(__name__)


@dataclass
class _NodeStats:
    """Per-node health and load tracking."""
    endpoint:        str
    active_requests: int   = 0
    failures:        int   = 0
    last_failure_ts: float = 0.0
    _lock: threading.Lock  = field(default_factory=threading.Lock, repr=False)

    # A node is considered unavailable for 30 s after a failure burst.
    BACKOFF_SECONDS = 30
    MAX_FAILURES    = 3

    def is_available(self) -> bool:
        if self.failures < self.MAX_FAILURES:
            return True
        return (time.monotonic() - self.last_failure_ts) > self.BACKOFF_SECONDS

    def mark_failure(self) -> None:
        with self._lock:
            self.failures        += 1
            self.last_failure_ts  = time.monotonic()

    def mark_success(self) -> None:
        with self._lock:
            self.failures = 0

    def acquire(self) -> None:
        with self._lock:
            self.active_requests += 1

    def release(self) -> None:
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)


class InferenceRouter:
    """
    Least-connections router across multiple OpenAI-compatible inference nodes.

    If vLLM endpoints are configured via env vars (VLLM_ENDPOINT_1 …),
    requests are routed to the node with the fewest active requests that is
    currently healthy.

    Falls back to Groq key rotation (KeyManager) when no vLLM nodes are
    configured, preserving the existing production behaviour unchanged.
    """

    def __init__(self) -> None:
        self._nodes: list[_NodeStats] = []
        self._lock  = threading.Lock()

        # Discover vLLM nodes from env — VLLM_ENDPOINT_1, _2, _3, …
        idx = 1
        while True:
            ep = os.getenv(f"VLLM_ENDPOINT_{idx}")
            if not ep:
                break
            self._nodes.append(_NodeStats(endpoint=ep))
            logger.info("[InferenceRouter] registered vLLM node %d: %s", idx, ep)
            idx += 1

        if self._nodes:
            logger.info("[InferenceRouter] vLLM mode — %d node(s) registered", len(self._nodes))
        else:
            logger.info("[InferenceRouter] Groq-fallback mode — no VLLM_ENDPOINT_* vars set")

    @property
    def using_vllm(self) -> bool:
        return bool(self._nodes)

    def _pick_node(self) -> _NodeStats | None:
        """Return the available node with the fewest active requests."""
        with self._lock:
            available = [n for n in self._nodes if n.is_available()]
        if not available:
            return None
        return min(available, key=lambda n: n.active_requests)

    def call(
        self,
        make_request: Callable[[str], Any],
        max_retries: int = 3,
    ) -> Any:
        """
        Route a single inference call.

        Parameters
        ----------
        make_request:
            A callable that accepts an endpoint URL string and returns the
            inference result. For vLLM nodes it receives the node's base URL;
            for Groq fallback it receives an empty string (KeyManager handles
            the URL internally).
        max_retries:
            Number of node-level retries before raising.
        """
        if not self.using_vllm:
            # Groq fallback — delegate to KeyManager (unchanged behaviour)
            from pipeline.key_manager import KeyManager  # noqa: PLC0415
            return KeyManager.call_with_rotation(
                lambda client: make_request(client),
                max_retries=max_retries,
            )

        last_exc: Exception | None = None
        for attempt in range(max_retries):
            node = self._pick_node()
            if node is None:
                raise RuntimeError("InferenceRouter: all vLLM nodes are unavailable")

            node.acquire()
            try:
                result = make_request(node.endpoint)
                node.mark_success()
                return result
            except Exception as exc:
                node.mark_failure()
                last_exc = exc
                logger.warning(
                    "[InferenceRouter] node %s failed (attempt %d/%d): %s",
                    node.endpoint, attempt + 1, max_retries, exc,
                )
            finally:
                node.release()

        raise RuntimeError(
            f"InferenceRouter: all {max_retries} attempts failed"
        ) from last_exc


# Module-level singleton — import and use in answer_generator.py
router = InferenceRouter()
