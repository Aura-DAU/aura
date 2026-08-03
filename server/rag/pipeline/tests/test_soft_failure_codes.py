"""CHAT-05: soft-failure sites must emit distinguishable structured log codes.

User-facing copy stays identical (frontend matches on it). Attribution lives
entirely in the structured log: each raise/return site has a stable code, the
underlying exception type + message, a timeout/saturation flag, and the target
node when the failure came from an LLM call.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from pipeline.exceptions import RAGPipelineError
from pipeline.generation.answer_generator import (
    SOFT_FAILURE_ANSWER,
    AnswerGenerator,
    is_saturation_error,
    is_timeout_error,
    log_soft_failure,
)


class _StubClient:
    base_url = "http://10.100.97.71:8001/v1"

    def __init__(self, response=None, raises: Exception | None = None):
        self._response = response
        self._raises = raises
        self.chat = SimpleNamespace(completions=self)

    def create(self, **_kwargs):
        if self._raises is not None:
            raise self._raises
        return self._response


def _ok_response(content: str = "Hello from DAU."):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


@pytest.mark.parametrize(
    "exc,expect_timeout,expect_sat",
    [
        (TimeoutError("read timed out after 60s"), True, False),
        (RAGPipelineError("All vLLM inference nodes exhausted after 5 attempts"), False, True),
        (RuntimeError("429 Too Many Requests — rate limit"), False, True),
        (ValueError("malformed chunk"), False, False),
        (None, False, False),
    ],
)
def test_timeout_and_saturation_detection(exc, expect_timeout, expect_sat):
    assert is_timeout_error(exc) is expect_timeout
    assert is_saturation_error(exc) is expect_sat


def test_log_soft_failure_emits_structured_fields(caplog, monkeypatch):
    monkeypatch.setattr(
        "pipeline.generation.answer_generator.InferenceRouter.stats",
        classmethod(lambda cls: {
            "http://10.100.97.71:8001/v1": {
                "inflight": 24, "fail_streak": 0, "cooling_down": False,
            },
            "http://10.100.97.72:8000/v1": {
                "inflight": 0, "fail_streak": 0, "cooling_down": False,
            },
        }),
    )
    with caplog.at_level(logging.ERROR):
        log_soft_failure(
            "AURA-GEN-002",
            "generation.buffered",
            exc=TimeoutError("read timed out"),
            node="http://10.100.97.71:8001/v1",
        )
    assert len(caplog.records) == 1
    msg = caplog.records[0].message
    assert "code=AURA-GEN-002" in msg
    assert "stage=generation.buffered" in msg
    assert "exc_type=TimeoutError" in msg
    assert "timeout=True" in msg
    assert "node=http://10.100.97.71:8001/v1" in msg
    assert "inflight=24" in msg


def test_generate_null_response_raises_with_code(monkeypatch, caplog):
    """AURA-GEN-001: router returned a falsy response."""
    monkeypatch.setattr(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        lambda fn, max_retries=5, **kw: None,
    )
    gen = AnswerGenerator.__new__(AnswerGenerator)
    gen.model = "test-model"
    with caplog.at_level(logging.ERROR):
        # generate() catches RAGPipelineError and returns the soft-failure
        # string — so we assert both the user-facing copy and the code.
        answer = gen.generate(
            query="What is DAU?",
            context="<context><doc id=\"1\">DAU is a university.</doc></context>",
            plan={"category": "general"},
        )
    assert answer == SOFT_FAILURE_ANSWER
    # Either GEN-001 (null response) or GEN-002 (caught raise of GEN-001).
    assert any(
        code in r.message for r in caplog.records for code in ("AURA-GEN-001", "AURA-GEN-002")
    )


def test_generate_exception_logs_type_and_node(monkeypatch, caplog):
    """AURA-GEN-002: underlying exception type/message must not be swallowed."""

    def _boom(fn, max_retries=5, **kw):
        # Invoke fn so the stub records the node, then raise as the router would.
        client = _StubClient(raises=TimeoutError("read timed out after 60s"))
        try:
            return fn(client)
        except TimeoutError as exc:
            raise RAGPipelineError(f"All vLLM inference nodes exhausted: {exc}") from exc

    monkeypatch.setattr(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        _boom,
    )
    gen = AnswerGenerator.__new__(AnswerGenerator)
    gen.model = "test-model"
    with caplog.at_level(logging.ERROR):
        answer = gen.generate(
            query="What is DAU?",
            context="<context><doc id=\"1\">DAU is a university.</doc></context>",
            plan={"category": "general"},
        )
    assert answer == SOFT_FAILURE_ANSWER
    assert any("AURA-GEN-002" in r.message for r in caplog.records)
    assert any("exc_type=RAGPipelineError" in r.message for r in caplog.records)
    assert any("node=http://10.100.97.71:8001/v1" in r.message for r in caplog.records)
    assert any("saturation=True" in r.message for r in caplog.records)


def test_streaming_null_stream_raises_with_code(monkeypatch, caplog):
    """AURA-GEN-003: router returned a falsy stream."""
    monkeypatch.setattr(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        lambda fn, max_retries=5, **kw: None,
    )
    gen = AnswerGenerator.__new__(AnswerGenerator)
    gen.model = "test-model"
    with caplog.at_level(logging.ERROR):
        with pytest.raises(RAGPipelineError) as raised:
            gen._generate_streaming("sys", "user", on_delta=lambda _: None)
    assert str(raised.value) == SOFT_FAILURE_ANSWER
    assert any("AURA-GEN-003" in r.message for r in caplog.records)


def test_aura_chat_exception_emits_chat_001(monkeypatch, caplog):
    """AURA-CHAT-001: linear chat path soft-failure is attributable."""
    from pipeline.aura_chat import AuraChat

    chat = AuraChat.__new__(AuraChat)
    chat.guardrail = SimpleNamespace(classify=lambda *_a, **_k: __import__(
        "pipeline.guardrails.query_guardrail", fromlist=["Verdict"]
    ).Verdict.SAFE)
    chat.wellness = SimpleNamespace(check=lambda *_a, **_k: False)
    chat.classifier = SimpleNamespace(
        classify=lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("synthetic pipeline blowup"))
    )
    chat.pipeline = SimpleNamespace()
    chat.generator = SimpleNamespace()
    chat.erp_connector = SimpleNamespace()
    chat.erp_builder = SimpleNamespace()
    chat.access_gate = SimpleNamespace()
    chat.audit = SimpleNamespace()

    with caplog.at_level(logging.ERROR):
        # Non-greeting query so we reach the classifier and hit the raise.
        result = chat.chat(
            "What is the fee structure for B.Tech ICT?",
            identity=SimpleNamespace(erp_id="202401001", role="student", dept="ICT"),
        )
    assert "encountered an error while generating a response" in result["answer"]
    assert any("AURA-CHAT-001" in r.message for r in caplog.records)
    assert any("exc_type=RuntimeError" in r.message for r in caplog.records)


def test_aura_chat_graph_missing_result_emits_graph_001(monkeypatch, caplog):
    """AURA-GRAPH-001: graph ended without setting result."""
    from pipeline.aura_chat_graph import AuraChatGraph

    graph = AuraChatGraph.__new__(AuraChatGraph)
    graph._graph = SimpleNamespace(invoke=lambda state: {**state, "result": None})

    with caplog.at_level(logging.ERROR):
        result = graph.chat("hello", identity={"erp_id": "x", "role": "guest"})
    assert "encountered an error while generating a response" in result["answer"]
    assert any("AURA-GRAPH-001" in r.message for r in caplog.records)


def test_aura_chat_graph_exception_emits_graph_002(monkeypatch, caplog):
    """AURA-GRAPH-002: unhandled graph exception is attributable."""
    from pipeline.aura_chat_graph import AuraChatGraph

    graph = AuraChatGraph.__new__(AuraChatGraph)

    def _boom(_state):
        raise TimeoutError("graph invoke timed out")

    graph._graph = SimpleNamespace(invoke=_boom)

    with caplog.at_level(logging.ERROR):
        result = graph.chat("hello", identity={"erp_id": "x", "role": "guest"})
    # Timeout branch uses the connection-issue copy, but the code still fires.
    assert result["answer"]
    assert any("AURA-GRAPH-002" in r.message for r in caplog.records)
    assert any("exc_type=TimeoutError" in r.message for r in caplog.records)
    assert any("timeout=True" in r.message for r in caplog.records)


def test_user_facing_copy_unchanged():
    """Frontend matches on this exact string — do not drift it."""
    assert SOFT_FAILURE_ANSWER == "Sorry, I encountered an error while generating a response."
