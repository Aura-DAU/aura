"""AnswerGenerator context-length handling — AURA-CTX-001 vs soft-failure."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
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


def test_prompt_answers_task_without_duplicating_history_or_hiding_rbac():
    gen = AnswerGenerator()
    captured = {}
    client = MagicMock()
    client.base_url = "http://inference.test/v1"
    client.chat.completions.create.side_effect = lambda **kwargs: (
        captured.update(kwargs)
        or SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="The library is open from 9 AM to 8 PM. [1]"
                    )
                )
            ]
        )
    )

    with patch.object(gen, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        side_effect=lambda fn, max_retries=5: fn(client),
    ):
        answer = gen.generate(
            query="When is the library open?",
            context=(
                '<context><doc id="1">The library is open from 9 AM to 8 PM.'
                "</doc></context>"
            ),
            plan={"retrieval_intent": "general", "entities": {}},
            history=[
                {"role": "user", "content": "Earlier question"},
                {"role": "assistant", "content": "Earlier answer"},
            ],
            profile={"role": "student"},
        )

    messages = captured["messages"]
    assert sum("Earlier question" in message["content"] for message in messages) == 1
    final_prompt = messages[-1]["content"]
    assert "Earlier question" not in final_prompt
    assert "Do not interrupt or replace the answer to ask for one" in final_prompt
    assert "--- ACCESS CONTROL RULES ---" in final_prompt
    assert answer.startswith("The library is open")


def test_empty_buffered_model_response_returns_soft_failure(caplog):
    gen = AnswerGenerator()
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=""))]
    )

    with patch.object(gen, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        return_value=response,
    ), caplog.at_level("ERROR"):
        answer = gen.generate(
            query="When is the library open?",
            context='<context><doc id="1">Open daily.</doc></context>',
            plan={"retrieval_intent": "general", "entities": {}},
        )

    assert answer == SOFT_FAILURE_ANSWER
    assert any("code=AURA-GEN-004" in record.message for record in caplog.records)


def test_think_only_stream_returns_soft_failure_without_empty_delta(caplog):
    gen = AnswerGenerator()
    stream = iter([
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="<think>internal only</think>")
                )
            ]
        )
    ])
    deltas = []

    with patch.object(gen, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        return_value=stream,
    ), caplog.at_level("ERROR"):
        answer = gen.generate(
            query="When is the library open?",
            context='<context><doc id="1">Open daily.</doc></context>',
            plan={"retrieval_intent": "general", "entities": {}},
            on_delta=deltas.append,
        )

    assert answer == SOFT_FAILURE_ANSWER
    assert deltas == []
    assert any("code=AURA-GEN-005" in record.message for record in caplog.records)


def test_streaming_profile_callback_does_not_swallow_source_marker():
    gen = AnswerGenerator()
    stream = iter([
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content="The library is open from 9 AM to 8 PM. [1]"
                    )
                )
            ]
        )
    ])
    deltas = []

    with patch.object(gen, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        return_value=stream,
    ):
        answer = gen.generate(
            query="When is the library open?",
            context=(
                '<context><doc id="1">The library is open from 9 AM to 8 PM.'
                "</doc></context>"
            ),
            plan={"retrieval_intent": "general", "entities": {}},
            profile={"role": "student"},
            on_delta=deltas.append,
            on_profile_update=lambda _name: None,
        )

    assert "[Sources: 1]" in answer
    assert "[Sources: 1]" not in "".join(deltas)
