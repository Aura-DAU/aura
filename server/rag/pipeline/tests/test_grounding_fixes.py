"""
Regression tests for the grounding fixes in the RAG pipeline review:
prompt layout and history hygiene (D4/E2), uncited answers (E4), the
unsupported-number check (E3), relevance filtering (C1), match-preserving
expansion (C2) and context trimming (D1/D3).
"""

import re
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pipeline.generation.answer_generator import (
    NO_CONTEXT_ANSWER,
    SYSTEM_PROMPT,
    AnswerGenerator,
    append_data_period_note,
    history_messages,
    unsupported_numbers,
)
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
from pipeline.token_budget import TokenBudget


@pytest.fixture(autouse=True)
def _budget_env(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "8192")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "3000")
    yield
    TokenBudget.reset_for_tests()


def test_system_prompt_fits_its_token_reserve():
    reserve = TokenBudget.from_env(discover=False).config.max_system_prompt_tokens
    assert TokenBudget.from_env(discover=False).estimate_tokens(SYSTEM_PROMPT) <= reserve * 1.2


def test_history_trims_long_assistant_turns_and_date_notes():
    long_answer = "The fee is 1,85,000. " * 80 + "\n\nData period: Academic Year 2025-2026."
    msgs = history_messages([
        {"role": "user", "content": "What is the fee?"},
        {"role": "assistant", "content": long_answer},
        {"role": "system", "content": "ignored"},
    ])
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert len(msgs[1]["content"]) < 700
    assert "Data period" not in msgs[1]["content"]


def test_prompt_puts_documents_before_question():
    captured = {}
    client = MagicMock()
    client.base_url = "http://inference.test/v1"
    client.chat.completions.create.side_effect = lambda **kwargs: (
        captured.update(kwargs)
        or SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Open 9 to 8. [1]"))])
    )
    gen = AnswerGenerator()
    with patch.object(gen, "_budget_max_tokens", return_value=256), patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        side_effect=lambda fn, max_retries=5: fn(client),
    ):
        gen.generate(
            query="When is the library open?",
            context='<context><doc id="1">Library: 9 AM to 8 PM.</doc></context>',
            plan=None,
            summary="Told: hostel fee is 50,000.",
        )
    prompt = captured["messages"][-1]["content"]
    assert prompt.index("<doc") < prompt.index("QUESTION: When is the library open?")
    assert "not a source of facts" in prompt
    assert "Planner Analysis" not in prompt
    assert '<doc id="1">\n...' not in prompt


def test_empty_context_returns_fixed_answer_without_model_call():
    gen = AnswerGenerator()
    with patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation"
    ) as call:
        answer = gen.generate(query="x", context="<context>\n</context>", plan=None)
    assert answer == NO_CONTEXT_ANSWER
    assert "dau.edu.in" not in answer
    call.assert_not_called()


def test_uncited_answer_gets_no_date_note():
    answer = "I could not find that information in the available university data."
    assert append_data_period_note(answer, '<doc id="1" rule_year="2025-26">x</doc>', set()) == answer


def test_unsupported_numbers_flags_only_new_figures():
    context = '<doc id="1">Tuition Fee: Rs. 1,85,000. Deadline 2026-08-20. Course IT205.</doc>'
    assert unsupported_numbers("Fee is Rs. 185000 for IT205, due 2026.", context) == []
    assert unsupported_numbers("Fee is Rs. 2,10,000 for 2 terms.", context) == ["210000"]


def test_drop_irrelevant_uses_cross_encoder_logit():
    kept = RetrievalPipeline._drop_irrelevant([
        {"id": "a", "cross_score": 2.0, "reranked_score": 0.5},
        {"id": "b", "cross_score": -9.0, "reranked_score": 0.9},
        {"id": "c", "reranked_score": 0.1},
    ])
    assert [c["id"] for c in kept] == ["a", "c"]


def _pipeline_with_store(chunks):
    pipeline = RetrievalPipeline.__new__(RetrievalPipeline)
    pipeline.chunk_by_coordinate = {
        (c["document_id"], c["chunk_index"]): c for c in chunks
    }
    return pipeline


def test_expansion_keeps_core_and_skips_selected_neighbours():
    store = [
        {"document_id": "d", "chunk_index": i, "text": f"chunk {i}", "chunk_id": f"d{i}"}
        for i in range(4)
    ]
    pipeline = _pipeline_with_store(store)
    candidates = [
        {"id": "d1", "metadata": {"document_id": "d", "chunk_index": 1, "text": "chunk 1"}},
        {"id": "d2", "metadata": {"document_id": "d", "chunk_index": 2, "text": "chunk 2"}},
    ]
    expanded = pipeline._expand_adjacent_chunks(candidates, window=1)
    first = expanded[0]["metadata"]
    assert first["core_text"] == "chunk 1"
    assert first["context_before"] == "chunk 0"
    assert first["context_after"] == ""  # chunk 2 is itself selected
    assert expanded[1]["metadata"]["context_after"] == "chunk 3"


def test_context_builder_trims_neighbours_before_core():
    core = "CORE " + "fee table row\n" * 20
    chunk = {
        "metadata": {
            "title": 'Fees "2025-26"',
            "url": "https://daiict.ac.in/fees",
            "text": "before\n" * 2000 + core + "after\n" * 2000,
            "core_text": core,
            "context_before": "before\n" * 2000,
            "context_after": "after\n" * 2000,
        }
    }
    built = ContextBuilder().build([chunk])
    context = built["context"]
    assert core.strip() in context
    assert 'title="Fees &quot;2025-26&quot;"' in context
    assert 'faculty_name=""' not in context


def test_context_builder_fills_leftover_budget_with_small_chunks(monkeypatch):
    # 600-token budget, 300 per document: a truncated big doc and a medium doc
    # leave ~50 tokens, too little for another big doc but enough for a small one.
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "600")
    TokenBudget.reset_for_tests()
    builder = ContextBuilder()
    chunks = [
        {"metadata": {"title": "Big A", "url": "https://d/a", "text": "word " * 1200}},
        {"metadata": {"title": "Medium", "url": "https://d/m", "text": "word " * 161}},
        {"metadata": {"title": "Big B", "url": "https://d/b", "text": "word " * 1200}},
        {"metadata": {"title": "Small", "url": "https://d/small", "text": "short answer"}},
    ]
    built = builder.build(chunks)
    context = built["context"]
    ids = re.findall(r'<doc id="(\d+)"', context)
    assert ids == ["1", "2", "3"]
    assert "Big B" not in context
    assert "short answer" in context
    assert context.count("<doc ") == len(built["citation_map"])
    assert builder._estimate_tokens(context) <= 600 + 10
