"""Contextualise + decompose step: fast path, LLM path, fallbacks."""

import json
from types import SimpleNamespace

import pytest

from pipeline.retrieval import query_understanding as qu
from pipeline.retrieval.query_understanding import (
    FOLLOWUP_FOLLOW_UP,
    FOLLOWUP_NEW,
    FOLLOWUP_TRANSFORM,
    QueryUnderstanding,
    extract_thread_summary,
    heuristic_split,
    looks_compound,
)


class _FakeClient:
    def __init__(self, content):
        self.content = content
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if isinstance(self.content, Exception):
            raise self.content
        msg = SimpleNamespace(content=self.content)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _patch_llm(monkeypatch, content):
    client = _FakeClient(content)

    def fake_call(fn, max_retries=3, **_):
        return fn(client)

    monkeypatch.setattr(qu.InferenceRouter, "call_with_rotation", staticmethod(fake_call))
    return client


def _reply(type_, questions):
    return json.dumps({"type": type_, "questions": questions})


# ── Fast path ───────────────────────────────────────────────────────────

def test_first_turn_single_question_makes_no_llm_call(monkeypatch):
    client = _patch_llm(monkeypatch, _reply("new", ["x"]))
    out = QueryUnderstanding().understand("What is the hostel fee for B.Tech ICT?")
    assert out.questions == ("What is the hostel fee for B.Tech ICT?",)
    assert out.used_llm is False and out.resolved is True
    assert client.calls == []


def test_any_history_always_calls_llm_even_for_long_query_without_pronoun(monkeypatch):
    """The old gate skipped queries >8 words with no listed pronoun."""
    client = _patch_llm(
        monkeypatch,
        _reply("follow_up", ["What are the eligibility criteria for B.Tech ICT under the Gujarat quota?"]),
    )
    history = [
        {"role": "user", "content": "Tell me about B.Tech ICT"},
        {"role": "assistant", "content": "B.Tech ICT is a four year programme..."},
    ]
    q = "And what are the eligibility criteria under the Gujarat quota category for students?"
    out = QueryUnderstanding().understand(q, history=history)
    assert len(client.calls) == 1
    assert out.followup_type == FOLLOWUP_FOLLOW_UP
    assert "B.Tech ICT" in out.questions[0]
    assert out.resolved and out.used_llm


def test_summary_only_context_also_triggers_llm(monkeypatch):
    client = _patch_llm(monkeypatch, _reply("follow_up", ["What is the fee for M.Sc. IT?"]))
    out = QueryUnderstanding().understand(
        "what about its fee", history=[], summary="Current Thread Summary\nUser asked about M.Sc. IT."
    )
    assert len(client.calls) == 1
    user_prompt = client.calls[0]["messages"][1]["content"]
    assert "User asked about M.Sc. IT." in user_prompt
    assert out.questions == ("What is the fee for M.Sc. IT?",)


# ── Prompt content (context actually reaches the model) ─────────────────

def test_prompt_sees_thread_summary_but_not_cross_conversation_memory(monkeypatch):
    client = _patch_llm(monkeypatch, _reply("new", ["q"]))
    summary = "Persistent User Memory\nLikes cricket\n\nCurrent Thread Summary\nDiscussed hostel rules."
    QueryUnderstanding().understand("and mess timings?", history=[{"role": "user", "content": "hi"}], summary=summary)
    prompt = client.calls[0]["messages"][1]["content"]
    assert "Discussed hostel rules." in prompt
    assert "Likes cricket" not in prompt


def test_prompt_keeps_long_assistant_turn_beyond_old_400_char_cut(monkeypatch):
    client = _patch_llm(monkeypatch, _reply("follow_up", ["q"]))
    long_answer = "Scholarships: " + "; ".join(f"Scheme {i}" for i in range(1, 60)) + "; FINAL_SCHEME_MARKER"
    assert 400 < len(long_answer) < 1200
    QueryUnderstanding().understand(
        "explain the last one",
        history=[{"role": "user", "content": "list scholarships"}, {"role": "assistant", "content": long_answer}],
    )
    assert "FINAL_SCHEME_MARKER" in client.calls[0]["messages"][1]["content"]


# ── Decomposition ───────────────────────────────────────────────────────

def test_compound_first_turn_is_split_by_llm(monkeypatch):
    _patch_llm(monkeypatch, _reply("new", ["What is the attendance rule?", "Who is the dean of academics?"]))
    out = QueryUnderstanding().understand("What is the attendance rule? Also who is the dean of academics?")
    assert out.is_compound and len(out.questions) == 2
    assert out.followup_type == FOLLOWUP_NEW


def test_more_than_max_questions_are_merged_into_last(monkeypatch):
    monkeypatch.setenv("AURA_MAX_SUBQUESTIONS", "3")
    _patch_llm(monkeypatch, _reply("new", ["a?", "b?", "c?", "d?", "e?"]))
    out = QueryUnderstanding().understand("a? b? c? d? e?")
    assert len(out.questions) == 3
    assert "d?" in out.questions[2] and "e?" in out.questions[2]


def test_duplicate_and_empty_questions_dropped(monkeypatch):
    _patch_llm(monkeypatch, _reply("new", ["Fee?", "fee?", "", "  "]))
    out = QueryUnderstanding().understand("Fee? fee?")
    assert out.questions == ("Fee?",)


# ── Transform-previous ──────────────────────────────────────────────────

def test_transform_previous_kept_when_assistant_turn_exists(monkeypatch):
    _patch_llm(monkeypatch, _reply("transform_previous", ["Shorten the previous answer about hostel rules."]))
    hist = [{"role": "user", "content": "hostel rules?"}, {"role": "assistant", "content": "Rules: ..."}]
    out = QueryUnderstanding().understand("make that shorter", history=hist)
    assert out.followup_type == FOLLOWUP_TRANSFORM
    assert len(out.questions) == 1


def test_transform_without_assistant_turn_downgraded_to_follow_up(monkeypatch):
    _patch_llm(monkeypatch, _reply("transform_previous", ["Shorten it."]))
    out = QueryUnderstanding().understand("make that shorter", history=[{"role": "user", "content": "hi"}])
    assert out.followup_type == FOLLOWUP_FOLLOW_UP


# ── Failure handling ────────────────────────────────────────────────────

def test_llm_failure_with_history_flags_unresolved_for_legacy_rewrite(monkeypatch):
    _patch_llm(monkeypatch, RuntimeError("vllm down"))
    out = QueryUnderstanding().understand(
        "what about its fee", history=[{"role": "user", "content": "tell me about ICT"}]
    )
    assert out.questions == ("what about its fee",)
    assert out.resolved is False and out.used_llm is False


def test_llm_failure_without_history_still_splits_obvious_compound(monkeypatch):
    _patch_llm(monkeypatch, RuntimeError("vllm down"))
    out = QueryUnderstanding().understand("What is the fee? Who is the dean?")
    assert out.questions == ("What is the fee?", "Who is the dean?")
    assert out.resolved is True


@pytest.mark.parametrize("bad", ["not json at all", "{}", '{"questions": []}', '{"questions": "x"' , "[]"])
def test_garbage_llm_output_falls_back(monkeypatch, bad):
    _patch_llm(monkeypatch, bad)
    out = QueryUnderstanding().understand("what about that?", history=[{"role": "user", "content": "x"}])
    assert out.used_llm is False and out.resolved is False


def test_fenced_json_and_think_block_are_tolerated(monkeypatch):
    raw = "<think>hmm</think>\n```json\n" + _reply("follow_up", ["What is the fee for ICT?"]) + "\n```"
    _patch_llm(monkeypatch, raw)
    out = QueryUnderstanding().understand("and fee?", history=[{"role": "user", "content": "ICT"}])
    assert out.questions == ("What is the fee for ICT?",)


def test_padded_rewrite_much_longer_than_input_is_rejected(monkeypatch):
    _patch_llm(monkeypatch, _reply("new", ["x " * 400]))
    out = QueryUnderstanding().understand("fee?", history=[{"role": "user", "content": "x"}])
    assert out.used_llm is False


# ── Helpers ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,expected", [
    ("What is the fee?", False),
    ("Tell me about ICT and CSE", False),
    ("What is the fee? Who is the dean?", True),
    ("What is the hostel fee and who is the dean of academics", True),
    ("1. fee of ICT\n2. dean of academics", True),
    ("Explain attendance rules; when do exams start", True),
    ("Compare the fees of B.Tech ICT and B.Tech CSE", False),
])
def test_looks_compound(text, expected):
    assert looks_compound(text) is expected


def test_heuristic_split_numbered_lines_and_cap():
    assert heuristic_split("1. What is the fee?\n2. Who is the dean?") == ["What is the fee?", "Who is the dean?"]
    parts = heuristic_split("a b c? d e f? g h i? j k l? m n o?", limit=3)
    assert len(parts) == 3 and "m n o?" in parts[2]


def test_extract_thread_summary_variants():
    both = "Persistent User Memory\nabc\n\nCurrent Thread Summary\nxyz"
    assert extract_thread_summary(both) == "xyz"
    assert extract_thread_summary("Persistent User Memory\nabc") == ""
    assert extract_thread_summary("plain summary") == "plain summary"
    assert extract_thread_summary(None) == ""
