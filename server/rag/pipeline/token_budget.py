"""Token budgeting for LLM requests against a fixed context window.

Why this exists
---------------
vLLM rejects over-length prompts with HTTP 400 in ~20ms. Without a pre-flight
budget the backend either (a) forwards that 400 as a 500, or (b) swallows it
into the generic "Sorry, I encountered an error…" soft failure. Both are
wrong. This module is the single place that:

  1. Resolves the live ``max_model_len`` (config override → /v1/models discovery
     → safe fallback).
  2. Counts tokens (prefer the node's ``/tokenize`` endpoint; fall back to a
     conservative local estimate that *over*-counts so we never under-budget).
  3. Trims lowest-ranked retrieved chunks until the request fits.
  4. Emits a structured token-stats log on every budgeted call.

KV-cache throughput is the real constraint, not just correctness. Measured
nodes have ``num_gpu_blocks=1491 × block_size=16 = 23,856`` KV tokens and
``kv_cache_max_concurrency ≈ 2.91`` at ``max_model_len=8192``. Eight concurrent
~5k-token RAG prompts drove KV to 92% and blew short-request p95 from 1.9s to
25s. So the retrieved-context *cap* is sized for the near-term 4096 cutover
even when the live window is still 8192 — a tighter prompt is a cluster-wide
latency win, not just a safety rail.

Defaults target ``max_model_len ≈ 4096`` with ``AURA_MAX_ANSWER_TOKENS=1024``:
input budget ≈ 4096 − 1024 − 64 ≈ 3008, of which ~1100 is reserved for the
system prompt and ~1400 for retrieved context. Do not hardcode 8192 anywhere.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Sequence

import httpx

from pipeline.exceptions import ContextLengthExceeded

logger = logging.getLogger(__name__)


# ── env helpers (local; keep this module free of InferenceRouter imports so
# unit tests can exercise budgeting without initialising the router) ─────────

def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float((os.getenv(name) or "").strip() or default)
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    val = (os.getenv(name) or "").strip().lower()
    if not val:
        return default
    return val in ("1", "true", "yes", "on")


# Near-term production target after the GPU-09 cutover. Used only when neither
# an env override nor a live /v1/models discovery succeeds. Prefer under-
# estimating the window (fail closed into trimming) over assuming 8192.
_FALLBACK_MAX_MODEL_LEN = 4096

# Chat-template overhead measured against Qwen3 on the live /tokenize endpoint:
# ~6 tokens/message + ~4 for enable_thinking=False + a small generation-prompt
# pad. The reported production failure was over by exactly 1 token, so the
# margin must absorb role/special tokens — off-by-small is the whole ballgame.
_CHAT_TEMPLATE_PER_MESSAGE = 8
_CHAT_TEMPLATE_BASE = 16


@dataclass(frozen=True)
class TokenBudgetConfig:
    """Resolved, immutable knobs for one process.

    All values are env-driven. ``max_model_len`` may additionally be filled by
    discovery; the rest are static for the process lifetime once constructed.
    """

    max_model_len: int
    reserved_output_tokens: int
    max_system_prompt_tokens: int
    max_retrieved_context_tokens: int
    safety_margin_tokens: int
    tokenize_enabled: bool
    tokenize_timeout_s: float

    @property
    def max_input_tokens(self) -> int:
        """Hard ceiling on (system + history + user + retrieved) tokens."""
        return max(
            0,
            self.max_model_len
            - self.reserved_output_tokens
            - self.safety_margin_tokens,
        )


@dataclass
class TokenStats:
    """Token accounting for one budgeted request. Always logged."""

    max_model_len: int
    reserved_output: int
    safety_margin: int
    max_input: int
    system_tokens: int
    history_tokens: int
    user_tokens: int
    retrieved_tokens: int
    template_overhead: int
    total_input: int
    chunks_kept: int
    chunks_trimmed: int
    tokenizer: str  # "vllm" | "estimate"
    fit: bool

    def as_log_fields(self) -> str:
        return " ".join(f"{k}={v}" for k, v in asdict(self).items())


@dataclass
class BudgetResult:
    """Outcome of ``fit_messages`` / ``accumulate_chunks``."""

    system_prompt: str
    history: list[dict]
    user_content: str
    kept_chunks: list  # opaque; whatever the caller passed in
    context_text: str
    stats: TokenStats
    max_tokens: int  # value to pass as completion max_tokens


# ── discovery / counting ────────────────────────────────────────────────────

class TokenBudget:
    """Process-wide token budgeter. Construct once; ``config`` is cached."""

    _lock = threading.Lock()
    _cached_config: TokenBudgetConfig | None = None
    _discovered_len: int | None = None
    _discovered_at: float = 0.0
    # Re-probe every 10 minutes so a rolling restart that drops max_model_len
    # 8192→4096 is picked up without a process bounce.
    _DISCOVERY_TTL_S = 600.0

    def __init__(self, config: TokenBudgetConfig | None = None):
        self._config = config

    # ── config resolution ───────────────────────────────────────────────────

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._lock:
            cls._cached_config = None
            cls._discovered_len = None
            cls._discovered_at = 0.0

    @classmethod
    def from_env(cls, *, discover: bool = True) -> "TokenBudget":
        """Build (or return the cached) budgeter from env + optional discovery."""
        with cls._lock:
            if cls._cached_config is not None and not discover:
                return cls(cls._cached_config)

        max_len = cls._resolve_max_model_len(discover=discover)

        # Defaults sized for the 4096 cutover. At 8192 they still leave KV
        # headroom; raising them just because the window is larger would
        # re-introduce the measured 13× short-query tail regression.
        cfg = TokenBudgetConfig(
            max_model_len=max_len,
            reserved_output_tokens=_env_int("AURA_MAX_ANSWER_TOKENS", 1024),
            # Aligned with ConversationMemory.reserved_system env name so one
            # knob drives both memory compaction and generation budgeting.
            max_system_prompt_tokens=_env_int("AURA_RESERVED_SYSTEM_TOKENS", 1100),
            # Aligned with ContextBuilder / ConversationMemory env name.
            # 1400 @ 4096 leaves ~500 for history+user after a ~1100 system.
            max_retrieved_context_tokens=_env_int("AURA_MAX_CONTEXT_TOKENS", 1400),
            safety_margin_tokens=_env_int("AURA_TOKEN_SAFETY_MARGIN", 64),
            tokenize_enabled=_env_bool("AURA_TOKENIZE_ENABLED", True),
            tokenize_timeout_s=_env_float("AURA_TOKENIZE_TIMEOUT", 0.5),
        )

        # If the resolved window is smaller than system+retrieved+output+margin,
        # shrink retrieved first so a misconfigured pair of knobs cannot make
        # every request raise ContextLengthExceeded before we even try.
        min_needed = (
            cfg.reserved_output_tokens
            + cfg.safety_margin_tokens
            + min(cfg.max_system_prompt_tokens, 256)
            + 64  # irreducible user-question pad
        )
        if cfg.max_model_len < min_needed + cfg.max_retrieved_context_tokens:
            affordable = max(0, cfg.max_model_len - min_needed)
            cfg = TokenBudgetConfig(
                max_model_len=cfg.max_model_len,
                reserved_output_tokens=cfg.reserved_output_tokens,
                max_system_prompt_tokens=cfg.max_system_prompt_tokens,
                max_retrieved_context_tokens=min(
                    cfg.max_retrieved_context_tokens, affordable
                ),
                safety_margin_tokens=cfg.safety_margin_tokens,
                tokenize_enabled=cfg.tokenize_enabled,
                tokenize_timeout_s=cfg.tokenize_timeout_s,
            )

        with cls._lock:
            cls._cached_config = cfg
        return cls(cfg)

    @classmethod
    def _resolve_max_model_len(cls, *, discover: bool) -> int:
        # Precedence: explicit AURA override → MAX_MODEL_LEN (compose/env pin
        # already used by ConversationMemory) → live /v1/models → 4096 fallback.
        for name in ("AURA_MAX_MODEL_LEN", "MAX_MODEL_LEN"):
            raw = (os.getenv(name) or "").strip()
            if raw:
                try:
                    val = int(raw)
                    if val > 0:
                        return val
                except ValueError:
                    pass

        if not discover:
            return _FALLBACK_MAX_MODEL_LEN

        now = time.monotonic()
        with cls._lock:
            if (
                cls._discovered_len is not None
                and (now - cls._discovered_at) < cls._DISCOVERY_TTL_S
            ):
                return cls._discovered_len

        discovered = cls._discover_max_model_len()
        if discovered is not None:
            with cls._lock:
                cls._discovered_len = discovered
                cls._discovered_at = now
            return discovered
        return _FALLBACK_MAX_MODEL_LEN

    @classmethod
    def _discover_max_model_len(cls) -> int | None:
        """Read ``max_model_len`` from the first reachable vLLM /v1/models.

        Compose files default ``--max-model-len`` to 16384 while live nodes are
        pinned to 8192 (and heading to ~4096). Never trust a constant — probe.
        Failures are silent: callers fall back to ``_FALLBACK_MAX_MODEL_LEN``.
        """
        raw = os.getenv("VLLM_ENDPOINTS") or os.getenv("VLLM_ENDPOINT", "")
        nodes = [n.strip().rstrip("/") for n in raw.split(",") if n.strip()]
        if not nodes:
            return None
        timeout = _env_float("AURA_TOKENIZE_TIMEOUT", 0.5)
        for node in nodes:
            url = f"{node}/models" if node.endswith("/v1") else f"{node}/v1/models"
            try:
                with httpx.Client(timeout=timeout) as client:
                    resp = client.get(url)
                if resp.status_code != 200:
                    continue
                data = resp.json().get("data") or []
                for entry in data:
                    val = entry.get("max_model_len")
                    if isinstance(val, int) and val > 0:
                        return val
            except Exception:
                continue
        return None

    @property
    def config(self) -> TokenBudgetConfig:
        if self._config is None:
            # Lazy: tests that construct TokenBudget() without args still work.
            return self.from_env(discover=False).config
        return self._config

    # ── counting ────────────────────────────────────────────────────────────

    def estimate_tokens(self, text: str) -> int:
        """Conservative local estimate. Prefer ``count_tokens`` when a node is up.

        Uses ≈3.5 chars/token. Against the live Qwen3 tokenizer the current
        system prompt is 4.09 chars/token, so this *over*-counts by ~15% on
        English RAG text — the safe direction for a pre-flight budget. Never
        use tiktoken / an OpenAI encoding here; those are wrong for Qwen.
        """
        if not text:
            return 0
        # (2*len + 6) // 7  ≡  ceil(len / 3.5)
        return max(1, (len(text) * 2 + 6) // 7)

    def count_tokens(self, text: str, *, messages: list[dict] | None = None) -> tuple[int, str]:
        """Return ``(count, "vllm"|"estimate")``.

        When ``messages`` is provided, count the fully chat-templated prompt
        (includes role/special tokens). Otherwise count ``text`` alone.
        """
        if self.config.tokenize_enabled:
            counted = self._tokenize_remote(text=text, messages=messages)
            if counted is not None:
                return counted, "vllm"
        if messages is not None:
            # Local fallback: sum part estimates + measured chat-template pad.
            parts = sum(self.estimate_tokens(m.get("content") or "") for m in messages)
            overhead = _CHAT_TEMPLATE_BASE + _CHAT_TEMPLATE_PER_MESSAGE * len(messages)
            return parts + overhead, "estimate"
        return self.estimate_tokens(text), "estimate"

    def _tokenize_remote(
        self,
        *,
        text: str,
        messages: list[dict] | None,
    ) -> int | None:
        raw = os.getenv("VLLM_ENDPOINTS") or os.getenv("VLLM_ENDPOINT", "")
        nodes = [n.strip().rstrip("/") for n in raw.split(",") if n.strip()]
        if not nodes:
            return None
        model = os.getenv("VLLM_MODEL", "aura-llm")
        # /tokenize is a sibling of /v1 on vLLM.
        for node in nodes:
            base = node[: -len("/v1")] if node.endswith("/v1") else node
            url = f"{base}/tokenize"
            body: dict
            if messages is not None:
                body = {
                    "model": model,
                    "messages": messages,
                    "add_generation_prompt": True,
                }
            else:
                body = {"model": model, "prompt": text}
            try:
                with httpx.Client(timeout=self.config.tokenize_timeout_s) as client:
                    resp = client.post(url, json=body)
                if resp.status_code != 200:
                    continue
                count = resp.json().get("count")
                if isinstance(count, int) and count >= 0:
                    return count
            except Exception:
                continue
        return None

    # ── budgeting ───────────────────────────────────────────────────────────

    def template_overhead(self, n_messages: int) -> int:
        return _CHAT_TEMPLATE_BASE + _CHAT_TEMPLATE_PER_MESSAGE * max(0, n_messages)

    def fit_retrieved(
        self,
        *,
        system_prompt: str,
        history: Sequence[dict] | None,
        user_prefix: str,
        chunks: Sequence[dict],
        render_chunk,
        wrap_context,
    ) -> BudgetResult:
        """Accumulate highest-ranked chunks until the retrieved budget is spent.

        ``chunks`` must already be in rank order (best first). ``render_chunk(idx,
        chunk) -> str`` builds one ``<doc>…</doc>`` block. ``wrap_context(docs)
        -> str`` wraps the kept docs (e.g. with ``<context>`` tags). Lowest-
        ranked chunks are the ones that fall off the end — we never drop a
        higher-ranked chunk to keep a lower one.
        """
        cfg = self.config
        history = list(history or [])

        sys_tokens, tok_mode = self.count_tokens(system_prompt)
        hist_tokens = 0
        for turn in history:
            t, m = self.count_tokens(turn.get("content") or "")
            hist_tokens += t
            if m == "estimate":
                tok_mode = "estimate"

        # Cap system prompt contribution at the configured budget for planning
        # the retrieved allowance. If the live system prompt itself exceeds the
        # cap we still send it (prompt audit owns the length) but retrieved
        # gets whatever input budget remains — possibly zero.
        system_for_budget = min(sys_tokens, cfg.max_system_prompt_tokens)

        # Messages that will actually hit the wire: system + history + one user.
        n_messages = 1 + len(history) + 1
        overhead = self.template_overhead(n_messages)

        # Remaining for (user_prefix + retrieved context), after system/history/
        # template. Also clamp to the configured retrieved cap — that cap is the
        # KV-throughput knob and must not grow just because the window is 8192.
        remaining_input = (
            cfg.max_input_tokens
            - system_for_budget
            - hist_tokens
            - overhead
        )
        # user_prefix is counted against remaining; leave it room before chunks.
        user_prefix_tokens, m = self.count_tokens(user_prefix)
        if m == "estimate":
            tok_mode = "estimate"
        retrieved_budget = max(
            0,
            min(
                cfg.max_retrieved_context_tokens,
                remaining_input - user_prefix_tokens,
            ),
        )

        kept: list = []
        docs: list[str] = []
        retrieved_tokens = 0
        trimmed = 0

        for idx, chunk in enumerate(chunks, start=1):
            doc_xml = render_chunk(idx, chunk)
            doc_tokens, m = self.count_tokens(doc_xml)
            if m == "estimate":
                tok_mode = "estimate"
            # Always keep the first chunk even if it alone exceeds the budget,
            # so the model still sees *something*; further chunks stop.
            if kept and retrieved_tokens + doc_tokens > retrieved_budget:
                trimmed = len(chunks) - len(kept)
                break
            kept.append(chunk)
            docs.append(doc_xml)
            retrieved_tokens += doc_tokens
        else:
            trimmed = 0

        context_text = wrap_context(docs) if docs else wrap_context([])
        # Re-count the wrapped context (tags add a few tokens) and, if it now
        # overshoots, drop lowest-ranked docs until it fits. Cheap because the
        # wrap is a small constant and we only re-count on overshoot.
        if docs:
            wrapped_tokens, m = self.count_tokens(context_text)
            if m == "estimate":
                tok_mode = "estimate"
            while len(docs) > 1 and wrapped_tokens > retrieved_budget:
                docs.pop()
                kept.pop()
                trimmed += 1
                context_text = wrap_context(docs)
                wrapped_tokens, m = self.count_tokens(context_text)
                if m == "estimate":
                    tok_mode = "estimate"
            retrieved_tokens = wrapped_tokens

        user_content_tokens = user_prefix_tokens + retrieved_tokens
        # Prefer a single chat-templated count when remote tokenize works — that
        # is the number vLLM will actually bill against max_model_len.
        user_content = user_prefix + context_text
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            role = turn.get("role")
            content = turn.get("content")
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})

        exact, exact_mode = self.count_tokens("", messages=messages)
        if exact_mode == "vllm":
            total_input = exact
            tok_mode = "vllm"
            # exact already includes template overhead
            overhead = max(0, exact - (sys_tokens + hist_tokens + user_content_tokens))
        else:
            total_input = sys_tokens + hist_tokens + user_content_tokens + overhead

        fit = total_input + cfg.reserved_output_tokens <= cfg.max_model_len

        # Last-resort: if still over (pathological system+user with zero
        # retrievable headroom), raise a structured error instead of sending.
        if not fit and not kept:
            stats = TokenStats(
                max_model_len=cfg.max_model_len,
                reserved_output=cfg.reserved_output_tokens,
                safety_margin=cfg.safety_margin_tokens,
                max_input=cfg.max_input_tokens,
                system_tokens=sys_tokens,
                history_tokens=hist_tokens,
                user_tokens=user_prefix_tokens,
                retrieved_tokens=retrieved_tokens,
                template_overhead=overhead,
                total_input=total_input,
                chunks_kept=0,
                chunks_trimmed=len(chunks),
                tokenizer=tok_mode,
                fit=False,
            )
            logger.error("token_budget_exceeded %s", stats.as_log_fields())
            raise ContextLengthExceeded(stats=asdict(stats))

        # If we have chunks but the total is still over (e.g. huge history),
        # keep trimming lowest-ranked until it fits or only one chunk remains.
        while (
            not fit
            and len(kept) > 1
            and total_input + cfg.reserved_output_tokens > cfg.max_model_len
        ):
            docs.pop()
            kept.pop()
            trimmed += 1
            context_text = wrap_context(docs)
            user_content = user_prefix + context_text
            messages[-1] = {"role": "user", "content": user_content}
            exact, exact_mode = self.count_tokens("", messages=messages)
            if exact_mode == "vllm":
                total_input = exact
                tok_mode = "vllm"
            else:
                retrieved_tokens, m = self.count_tokens(context_text)
                if m == "estimate":
                    tok_mode = "estimate"
                total_input = (
                    sys_tokens + hist_tokens + user_prefix_tokens + retrieved_tokens + overhead
                )
            fit = total_input + cfg.reserved_output_tokens <= cfg.max_model_len

        if not fit:
            stats = TokenStats(
                max_model_len=cfg.max_model_len,
                reserved_output=cfg.reserved_output_tokens,
                safety_margin=cfg.safety_margin_tokens,
                max_input=cfg.max_input_tokens,
                system_tokens=sys_tokens,
                history_tokens=hist_tokens,
                user_tokens=user_prefix_tokens,
                retrieved_tokens=retrieved_tokens,
                template_overhead=overhead,
                total_input=total_input,
                chunks_kept=len(kept),
                chunks_trimmed=trimmed + (len(chunks) - len(kept) - trimmed),
                tokenizer=tok_mode,
                fit=False,
            )
            logger.error("token_budget_exceeded %s", stats.as_log_fields())
            raise ContextLengthExceeded(stats=asdict(stats))

        # Clamp completion tokens so input + output never exceeds the window
        # even if a caller asks for more than reserved_output.
        room_for_output = max(1, cfg.max_model_len - total_input - cfg.safety_margin_tokens)
        max_tokens = min(cfg.reserved_output_tokens, room_for_output)

        stats = TokenStats(
            max_model_len=cfg.max_model_len,
            reserved_output=cfg.reserved_output_tokens,
            safety_margin=cfg.safety_margin_tokens,
            max_input=cfg.max_input_tokens,
            system_tokens=sys_tokens,
            history_tokens=hist_tokens,
            user_tokens=user_prefix_tokens,
            retrieved_tokens=retrieved_tokens,
            template_overhead=overhead,
            total_input=total_input,
            chunks_kept=len(kept),
            chunks_trimmed=max(trimmed, len(chunks) - len(kept)),
            tokenizer=tok_mode,
            fit=True,
        )
        logger.info("token_budget %s max_tokens=%d", stats.as_log_fields(), max_tokens)

        return BudgetResult(
            system_prompt=system_prompt,
            history=list(history),
            user_content=user_content,
            kept_chunks=kept,
            context_text=context_text,
            stats=stats,
            max_tokens=max_tokens,
        )


def is_context_length_error(exc: BaseException | None) -> bool:
    """True when ``exc`` is (or wraps) a vLLM context-window 400."""
    if exc is None:
        return False
    if isinstance(exc, ContextLengthExceeded):
        return True
    text = f"{type(exc).__name__} {exc}".lower()
    markers = (
        "maximum context length",
        "context length",
        "max_model_len",
        "please reduce the length of the messages",
        "token limit",
    )
    status = getattr(exc, "status_code", None)
    if status == 400 and any(m in text for m in markers):
        return True
    # RAGPipelineError wraps the SDK error: "unretryable status 400: ..."
    if "unretryable status 400" in text and any(m in text for m in markers):
        return True
    cause = getattr(exc, "__cause__", None) or getattr(exc, "__context__", None)
    if cause is not None and cause is not exc:
        return is_context_length_error(cause)
    return False
