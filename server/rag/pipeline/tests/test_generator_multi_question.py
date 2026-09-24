"""Answer generator: multi-question addendum, transform addendum, token budget.
Plus the query rewriter's multi-line and truncation-length fixes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from pipeline.generation import answer_generator as ag
from pipeline.generation.answer_generator import AnswerGenerator
from pipeline.retrieval import query_rewriter as qr
from pipeline.token_budget import TokenBudget


@pytest.fixture(autouse=True)
def _isolate_budget(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "8192")
    monkeypatch.setenv("AURA_MAX_ANSWER_TOKENS", "1024")
    monkeypatch.setenv("AURA_MAX_ANSWER_TOKENS_MULTI", "1536")
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    monkeypatch.setenv("AURA_RESERVED_SYSTEM_TOKENS", "1100")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "1400")
    monkeypatch.setenv("AURA_TOKEN_SAFETY_MARGIN", "64")
    yield
    TokenBudget.reset_for_tests()


def _capturing_client(reply="1. Fee is X. [1]\n2. Dean is Y. [1]"):
    captured = {}
    client = MagicMock()
    client.base_url = "http://inference.test/v1"
    client.chat.completions.create.side_effect = lambda **kwargs: (
        captured.update(kwargs)
        or SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])
    )
    return client, captured


def _generate(gen, client, **kwargs):
    with patch(
        "pipeline.generation.answer_generator.InferenceRouter.call_with_rotation",
        side_effect=lambda fn, max_retries=5: fn(client),
    ):
        return gen.generate(
            query=kwargs.pop("query", "raw"),
            context=kwargs.pop(
                "context",
                '<context><doc id="1" q="1">Fee is X.</doc><doc id="2" q="2">Dean is Y.</doc></context>',
            ),
            plan=kwargs.pop("plan", {"retrieval_intent": "general", "entities": {}}),
            **kwargs,
        )


# ── Multi-question prompt ───────────────────────────────────────────────

def test_multi_question_block_lists_every_question_in_order():
    gen = AnswerGenerator()
    client, captured = _capturing_client()
    _generate(gen, client, questions=["What is the hostel fee?", "Who is the dean?"])
    final_prompt = captured["messages"][-1]["content"]
    assert "QUESTIONS (answer every one, in this order):" in final_prompt
    assert "1. What is the hostel fee?" in final_prompt
    assert "2. Who is the dean?" in final_prompt
    assert ag.MULTI_QUESTION_ADDENDUM.strip() in captured["messages"][0]["content"]


def test_single_question_prompt_is_unchanged_by_the_multi_path():
    gen = AnswerGenerator()
    client, captured = _capturing_client("Fee is X. [1]")
    _generate(gen, client, query="What is the hostel fee?", questions=["What is the hostel fee?"])
    final_prompt = captured["messages"][-1]["content"]
    assert "QUESTION: What is the hostel fee?" in final_prompt
    assert "QUESTIONS (answer every one" not in final_prompt
    assert ag.MULTI_QUESTION_ADDENDUM.strip() not in captured["messages"][0]["content"]


def test_no_questions_kwarg_behaves_exactly_like_before():
    gen = AnswerGenerator()
    client, captured = _capturing_client("Fee is X. [1]")
    _generate(gen, client, query="What is the hostel fee?")
    assert "QUESTION: What is the hostel fee?" in captured["messages"][-1]["content"]
    assert ag.MULTI_QUESTION_ADDENDUM.strip() not in captured["messages"][0]["content"]


def test_multi_question_answer_budget_can_exceed_the_single_question_cap():
    gen = AnswerGenerator()
    client, captured = _capturing_client()
    _generate(gen, client, questions=["a?", "b?", "c?"])
    assert captured["max_tokens"] > 1024


def test_budget_multi_cap_still_bounded_by_the_live_context_window(monkeypatch):
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "2200")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "200")
    TokenBudget.reset_for_tests()
    gen = AnswerGenerator()
    client, captured = _capturing_client()
    _generate(gen, client, questions=["a?", "b?"])
    assert captured["max_tokens"] < 1536


# ── Transform-previous prompt ────────────────────────────────────────────

def test_transform_previous_adds_its_addendum_and_no_multi_addendum():
    gen = AnswerGenerator()
    client, captured = _capturing_client("Shorter version.")
    _generate(
        gen, client,
        query="Shorten the previous answer about hostel fees.",
        context='<context>\n<previous_answer>\nThe annual hostel fee is Rs. 60,000.\n</previous_answer>\n</context>',
        followup_type="transform_previous",
    )
    system_prompt = captured["messages"][0]["content"]
    assert ag.TRANSFORM_ADDENDUM.strip() in system_prompt
    assert ag.MULTI_QUESTION_ADDENDUM.strip() not in system_prompt
    final_prompt = captured["messages"][-1]["content"]
    assert "<previous_answer>" in final_prompt and "60,000" in final_prompt


def test_transform_and_multi_addenda_can_combine():
    gen = AnswerGenerator()
    client, captured = _capturing_client()
    _generate(gen, client, questions=["Shorten X.", "Translate Y."], followup_type="transform_previous")
    system_prompt = captured["messages"][0]["content"]
    assert ag.TRANSFORM_ADDENDUM.strip() in system_prompt
    assert ag.MULTI_QUESTION_ADDENDUM.strip() in system_prompt


# ── Per-question <no_documents> notes reach the model ────────────────────

def test_missing_document_note_is_visible_in_the_context_the_model_sees():
    gen = AnswerGenerator()
    client, captured = _capturing_client()
    context = (
        '<context><doc id="1" q="1">Fee is X.</doc>'
        '<no_documents q="2">No relevant university document was retrieved for this question.</no_documents>'
        '</context>'
    )
    _generate(gen, client, questions=["fee?", "moon landing?"], context=context)
    assert "<no_documents q=\"2\">" in captured["messages"][-1]["content"]


# ── Query rewriter: keep every line, longer history window ──────────────

def test_rewrite_keeps_every_line_not_just_the_first():
    rewriter = qr.QueryRewriter()
    client, captured = _capturing_client(
        "What is the hostel fee for B.Tech ICT?\nWho is the dean of academic affairs?"
    )
    with patch.object(qr.InferenceRouter, "call_with_rotation", side_effect=lambda fn, **k: fn(client)):
        out = rewriter.rewrite("fee and who is the dean", history=[{"role": "user", "content": "ICT"}])
    assert "hostel fee for B.Tech ICT" in out and "dean of academic affairs" in out


def test_assistant_turn_char_budget_was_raised_from_400():
    assert qr._ASSISTANT_TURN_CHARS >= 800


def test_rewrite_max_tokens_was_raised_from_120():
    assert qr._REWRITE_MAX_TOKENS >= 300
