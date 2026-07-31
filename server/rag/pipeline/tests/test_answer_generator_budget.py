"""AnswerGenerator context-length handling — AURA-CTX-001 vs soft-failure."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.exceptions import ContextLengthExceeded, RAGPipelineError
from pipeline.generation.answer_generator import (
    CONTEXT_LENGTH_ANSWER,
    SOFT_FAILURE_ANSWER,
    AnswerGenerator,
)
from pipeline.token_budget import TokenBudget


@pytest.fixture(autouse=True)
def _isolate_budget(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "4096")
    monkeypatch.setenv("AURA_MAX_ANSWER_TOKENS", "1024")
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    monkeypatch.setenv("AURA_RESERVED_SYSTEM_TOKENS", "1100")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "1400")
    monkeypatch.setenv("AURA_TOKEN_SAFETY_MARGIN", "64")


def test_context_length_exceeded_returns_structured_copy_not_soft_failure():
    gen = AnswerGenerator()
    with patch.object(
        gen,
        "_budget_max_tokens",
        side_effect=ContextLengthExceeded(stats={"fit": False, "total_input": 5000}),
    ):
        answer = gen.generate(
            query="what are the fees?",
            context='<context><doc id="1">Hostel fee is X</doc></context>',
            plan={"retrieval_intent": "general", "entities": {}},
        )
    assert answer == CONTEXT_LENGTH_ANSWER
    assert answer != SOFT_FAILURE_ANSWER


def test_vllm_context_length_400_maps_to_ctx_code_not_gen002():
    """Simulate inference_router wrapping a vLLM 400 as RAGPipelineError."""
    gen = AnswerGenerator()
    wrapped = RAGPipelineError(
        "Inference request failed with unretryable status 400: "
        "This model's maximum context length is 4096 tokens. "
        "Please reduce the length of the messages or completion."
    )

    with patch.object(gen, "_budget_max_tokens", return_value=1024), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        side_effect=wrapped,
    ):
        answer = gen.generate(
            query="what are the fees?",
            context='<context><doc id="1">Hostel fee is X</doc></context>',
            plan={"retrieval_intent": "general", "entities": {}},
        )
    assert answer == CONTEXT_LENGTH_ANSWER


def test_unrelated_exception_still_soft_fails():
    gen = AnswerGenerator()
    with patch.object(gen, "_budget_max_tokens", return_value=1024), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        side_effect=RuntimeError("boom"),
    ):
        answer = gen.generate(
            query="what are the fees?",
            context='<context><doc id="1">Hostel fee is X</doc></context>',
            plan={"retrieval_intent": "general", "entities": {}},
        )
    assert answer == SOFT_FAILURE_ANSWER
