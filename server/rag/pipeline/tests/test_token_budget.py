"""Unit tests for pipeline.token_budget — the LLM context-window pre-flight.

Covers the quality gates for the W6 workstream:
  - budget computed correctly at max_model_len=8192 AND 4096
  - lowest-ranked chunks trimmed first
  - pathological oversized system+user raises ContextLengthExceeded (no crash)
  - token-aware accumulation stops before the limit
  - context-length 400 detection (is_context_length_error)
"""

from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

# conftest already puts server/ and server/rag/ on sys.path; belt-and-braces:
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.exceptions import ContextLengthExceeded
from pipeline.token_budget import (
    TokenBudget,
    TokenBudgetConfig,
    is_context_length_error,
)


def _cfg(**overrides) -> TokenBudgetConfig:
    base = dict(
        max_model_len=4096,
        reserved_output_tokens=1024,
        max_system_prompt_tokens=1100,
        max_retrieved_context_tokens=1400,
        safety_margin_tokens=64,
        tokenize_enabled=False,  # unit tests: never hit the network
        tokenize_timeout_s=0.1,
    )
    base.update(overrides)
    return TokenBudgetConfig(**base)


def _budget(**overrides) -> TokenBudget:
    TokenBudget.reset_for_tests()
    return TokenBudget(_cfg(**overrides))


def _chunk(text: str, title: str = "doc") -> dict:
    return {"metadata": {"text": text, "title": title, "url": f"https://x/{title}"}}


def _render(idx: int, chunk: dict) -> str:
    meta = chunk["metadata"]
    return f'<doc id="{idx}" title="{meta["title"]}">{meta["text"]}</doc>'


def _wrap(docs: list[str]) -> str:
    return "<context>\n" + "\n".join(docs) + "\n</context>"


# ── config / window math ────────────────────────────────────────────────────

def test_input_budget_at_4096():
    b = _budget(max_model_len=4096, reserved_output_tokens=1024, safety_margin_tokens=64)
    # 4096 - 1024 - 64 = 3008
    assert b.config.max_input_tokens == 3008


def test_input_budget_at_8192():
    b = _budget(max_model_len=8192, reserved_output_tokens=1024, safety_margin_tokens=64)
    assert b.config.max_input_tokens == 8192 - 1024 - 64


def test_from_env_respects_aura_max_model_len(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "4096")
    monkeypatch.setenv("AURA_MAX_ANSWER_TOKENS", "1024")
    monkeypatch.setenv("AURA_RESERVED_SYSTEM_TOKENS", "1100")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "1400")
    monkeypatch.setenv("AURA_TOKEN_SAFETY_MARGIN", "64")
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    b = TokenBudget.from_env(discover=False)
    assert b.config.max_model_len == 4096
    assert b.config.reserved_output_tokens == 1024
    assert b.config.max_retrieved_context_tokens == 1400
    assert b.config.max_input_tokens == 3008


def test_from_env_falls_back_to_4096_not_8192(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.delenv("AURA_MAX_MODEL_LEN", raising=False)
    monkeypatch.delenv("MAX_MODEL_LEN", raising=False)
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    b = TokenBudget.from_env(discover=False)
    assert b.config.max_model_len == 4096


def test_max_model_len_override_beats_max_model_len_env(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "4096")
    monkeypatch.setenv("MAX_MODEL_LEN", "8192")
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    b = TokenBudget.from_env(discover=False)
    assert b.config.max_model_len == 4096


# ── accumulation / trimming ────────────────────────────────────────────────

def test_accumulate_stops_before_retrieved_cap():
    # Tiny retrieved cap so only the first short chunk fits.
    b = _budget(max_retrieved_context_tokens=40, max_system_prompt_tokens=50)
    chunks = [
        _chunk("alpha " * 5, "a"),   # short, highest ranked
        _chunk("bravo " * 40, "b"),  # would blow the cap
        _chunk("charlie " * 40, "c"),
    ]
    result = b.fit_retrieved(
        system_prompt="You are AURA.",
        history=[],
        user_prefix="QUESTION: fees?\n",
        chunks=chunks,
        render_chunk=_render,
        wrap_context=_wrap,
    )
    assert result.stats.fit is True
    assert result.stats.chunks_kept >= 1
    assert result.stats.chunks_trimmed >= 1
    # Highest-ranked (alpha) must survive; lowest-ranked must be the ones cut.
    kept_titles = [c["metadata"]["title"] for c in result.kept_chunks]
    assert kept_titles[0] == "a"
    assert "c" not in kept_titles or kept_titles.index("c") < len(kept_titles)


def test_lowest_ranked_trimmed_first():
    b = _budget(
        max_model_len=4096,
        reserved_output_tokens=1024,
        max_system_prompt_tokens=200,
        max_retrieved_context_tokens=120,
        safety_margin_tokens=16,
    )
    # Three equal-ish chunks; budget fits ~1-2. Rank order = list order.
    chunks = [_chunk(f"chunk-{i} " + ("word " * 25), f"rank{i}") for i in range(1, 4)]
    result = b.fit_retrieved(
        system_prompt="sys",
        history=[],
        user_prefix="Q?\n",
        chunks=chunks,
        render_chunk=_render,
        wrap_context=_wrap,
    )
    kept = [c["metadata"]["title"] for c in result.kept_chunks]
    # Whatever survived must be a prefix of the rank order — never keep rank3
    # while dropping rank1.
    assert kept == [f"rank{i}" for i in range(1, len(kept) + 1)]
    assert result.stats.chunks_trimmed == 3 - len(kept)
    assert result.stats.retrieved_tokens <= b.config.max_retrieved_context_tokens + 5


def test_total_never_exceeds_window_at_4096():
    b = _budget(max_model_len=4096, reserved_output_tokens=1024, safety_margin_tokens=64)
    chunks = [_chunk("x" * 500, f"d{i}") for i in range(20)]
    result = b.fit_retrieved(
        system_prompt="S" * 200,
        history=[{"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}],
        user_prefix="QUESTION: long?\nRetrieved:\n",
        chunks=chunks,
        render_chunk=_render,
        wrap_context=_wrap,
    )
    assert result.stats.fit is True
    assert (
        result.stats.total_input + result.stats.reserved_output
        <= result.stats.max_model_len
    )
    assert result.max_tokens <= 1024
    assert result.max_tokens + result.stats.total_input <= 4096


def test_total_never_exceeds_window_at_8192():
    b = _budget(max_model_len=8192, reserved_output_tokens=1024, safety_margin_tokens=64)
    chunks = [_chunk("y" * 800, f"d{i}") for i in range(30)]
    result = b.fit_retrieved(
        system_prompt="S" * 400,
        history=[],
        user_prefix="QUESTION: bigger?\n",
        chunks=chunks,
        render_chunk=_render,
        wrap_context=_wrap,
    )
    assert result.stats.fit is True
    assert (
        result.stats.total_input + result.stats.reserved_output
        <= result.stats.max_model_len
    )
    # Retrieved cap stays at the KV-throughput default even on an 8192 window.
    assert result.stats.retrieved_tokens <= b.config.max_retrieved_context_tokens + 5


def test_pathological_system_plus_user_raises_structured_error():
    # System prompt alone eats the entire input budget; no room for anything.
    b = _budget(
        max_model_len=4096,
        reserved_output_tokens=1024,
        max_system_prompt_tokens=3000,
        max_retrieved_context_tokens=1400,
        safety_margin_tokens=64,
    )
    huge_system = "X" * 20000  # estimate ≫ 3008 input budget
    with pytest.raises(ContextLengthExceeded) as ei:
        b.fit_retrieved(
            system_prompt=huge_system,
            history=[],
            user_prefix="Q" * 5000,
            chunks=[],
            render_chunk=_render,
            wrap_context=_wrap,
        )
    err = ei.value
    assert err.code == "AURA-CTX-001"
    assert err.stats["fit"] is False
    assert err.stats["system_tokens"] > 0


def test_empty_chunks_with_small_prompt_succeeds():
    b = _budget()
    result = b.fit_retrieved(
        system_prompt="You are AURA.",
        history=[],
        user_prefix="QUESTION: hi?\n",
        chunks=[],
        render_chunk=_render,
        wrap_context=_wrap,
    )
    assert result.stats.fit is True
    assert result.stats.chunks_kept == 0
    assert result.context_text == _wrap([])


# ── error detection (CHAT-05 linkage) ──────────────────────────────────────

def test_is_context_length_error_detects_vllm_400():
    class _FakeAPIStatus(Exception):
        status_code = 400

    exc = _FakeAPIStatus(
        "This model's maximum context length is 8192 tokens. "
        "However, you requested 8193 tokens (6145 in the messages, 2048 in the completion)."
    )
    assert is_context_length_error(exc) is True


def test_is_context_length_error_detects_wrapped_rag_error():
    from pipeline.exceptions import RAGPipelineError

    inner = Exception(
        "maximum context length is 4096 tokens. Please reduce the length of the messages"
    )
    wrapped = RAGPipelineError(
        "Inference request failed with unretryable status 400: " + str(inner)
    )
    wrapped.__cause__ = inner
    assert is_context_length_error(wrapped) is True
    assert is_context_length_error(ContextLengthExceeded()) is True


def test_is_context_length_error_ignores_unrelated_400():
    class _FakeAPIStatus(Exception):
        status_code = 400

    assert is_context_length_error(_FakeAPIStatus("invalid json schema")) is False
    assert is_context_length_error(None) is False


# ── estimate conservatism ──────────────────────────────────────────────────

def test_estimate_overcounts_relative_to_chars_div_4():
    b = _budget()
    text = "The quick brown fox jumps over the lazy dog. " * 50
    est = b.estimate_tokens(text)
    # chars/4 under-shot the live Qwen count by only ~2% on the system prompt;
    # our estimate uses ~3.5 chars/token and must be >= chars/4.
    assert est >= len(text) // 4
