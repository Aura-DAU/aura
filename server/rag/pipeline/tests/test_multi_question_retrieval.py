"""Multi-question retrieval, adaptive relevance cut, semester normalisation."""

from types import SimpleNamespace

import pytest

from pipeline.retrieval import retrieval_pipeline as rp
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.retrieval.reranker import Reranker, semester_numbers
from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline
from pipeline.token_budget import TokenBudget


@pytest.fixture(autouse=True)
def _budget(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "4096")
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")
    monkeypatch.setenv("AURA_RESERVED_SYSTEM_TOKENS", "1100")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "600")
    monkeypatch.setenv("AURA_TOKEN_SAFETY_MARGIN", "64")
    yield
    TokenBudget.reset_for_tests()


def _chunk(cid, text="Some university text.", title=None, score=None, **meta):
    md = {"text": text, "title": title or f"Doc {cid}", **meta}
    chunk = {"id": cid, "metadata": md}
    if score is not None:
        chunk["cross_score"] = score
    return chunk


def _pipeline():
    p = RetrievalPipeline.__new__(RetrievalPipeline)
    p.builder = ContextBuilder()
    p.chunk_by_coordinate = {}
    return p


def _search(chunks, top_k=5, complete_list=False):
    return {"search": {
        "original_query": "q", "corrected_query": "q", "standalone_query": "q",
        "plan": {"top_k": top_k}, "relevant": chunks, "pool_size": len(chunks) + 3,
        "requires_complete_list": complete_list, "retrieval_intent": "general",
        "title_hint": None,
    }}


# ── Adaptive relevance cut ──────────────────────────────────────────────

def test_relative_floor_drops_barely_related_chunks_behind_a_strong_hit():
    chunks = [_chunk(1, score=4.0), _chunk(2, score=0.0), _chunk(3, score=-3.0), _chunk(4, score=-6.0)]
    kept = RetrievalPipeline._drop_irrelevant(chunks)
    assert [c["id"] for c in kept] == [1, 2]  # p=.98, .50 kept; .047 and .002 dropped


def test_complete_list_queries_use_the_looser_ratio():
    chunks = [_chunk(1, score=4.0), _chunk(3, score=-3.0), _chunk(4, score=-6.0)]
    kept = RetrievalPipeline._drop_irrelevant(chunks, requires_complete_list=True)
    assert [c["id"] for c in kept] == [1, 3]


def test_absolute_floor_still_abstains_when_nothing_is_relevant():
    chunks = [_chunk(1, score=-6.0), _chunk(2, score=-7.0)]
    assert RetrievalPipeline._drop_irrelevant(chunks) == []


def test_unscored_chunks_are_kept_when_reranker_is_down():
    chunks = [_chunk(1), _chunk(2)]
    assert len(RetrievalPipeline._drop_irrelevant(chunks)) == 2


def test_extreme_negative_logit_does_not_overflow():
    chunks = [_chunk(1, score=3.0), _chunk(2, score=-2000.0)]
    assert [c["id"] for c in RetrievalPipeline._drop_irrelevant(chunks)] == [1]


def test_relative_ratio_zero_restores_absolute_only_behaviour(monkeypatch):
    monkeypatch.setattr(rp, "RELATIVE_RELEVANCE_RATIO", 0.0)
    chunks = [_chunk(1, score=4.0), _chunk(3, score=-3.0)]
    assert len(RetrievalPipeline._drop_irrelevant(chunks)) == 2


# ── Merging evidence for several questions ──────────────────────────────

def test_merge_is_rank_major_and_dedupes_shared_chunks():
    a, b, c, d, e = (_chunk(i) for i in (1, 2, 3, 4, 5))
    merged = RetrievalPipeline._merge_question_chunks([[a, b, c], [d], [dict(a), e]])
    assert [m["id"] for m in merged] == [1, 4, 2, 5, 3]
    assert merged[0]["questions"] == [1, 3]      # one copy serving Q1 and Q3
    assert merged[1]["questions"] == [2]
    assert "questions" not in a                   # inputs are not mutated


def test_multi_context_tags_docs_and_reports_per_question_coverage():
    p = _pipeline()
    p._search_many = lambda *a, **k: [
        _search([_chunk(1, "Hostel fee is Rs. 60,000 per year.", "Fees")]),
        _search([_chunk(2, "The Dean of Academic Affairs is Prof. X.", "Officers")]),
    ]
    out = p.get_multi_context(["hostel fee?", "who is the dean?"], history=[], standalone=True)
    assert out["questions"] == ["hostel fee?", "who is the dean?"]
    assert [e["in_context"] for e in out["per_question"]] == [True, True]
    assert 'q="1"' in out["context"] and 'q="2"' in out["context"]
    assert len(out["chunks"]) == 2 and len(out["sources"]) == 2
    assert "abstention_reason" not in out


def test_question_without_evidence_gets_an_explicit_marker_not_silence():
    p = _pipeline()
    p._search_many = lambda *a, **k: [
        _search([_chunk(1, "Attendance must be 75%.", "Rules")]),
        {"final": {"abstention_reason": "no_relevant_documents", "top_k_before_rerank": 9}},
    ]
    out = p.get_multi_context(["attendance rule?", "moon landing?"], standalone=True)
    assert out["per_question"][1]["in_context"] is False
    assert '<no_documents q="2">' in out["context"]
    assert out["context"].rstrip().endswith("</context>")
    assert out["chunks"]                          # question 1 still answered
    assert "abstention_reason" not in out


def test_all_questions_unanswerable_reports_abstention():
    p = _pipeline()
    p._search_many = lambda *a, **k: [
        {"final": {"abstention_reason": "no_relevant_documents", "top_k_before_rerank": 1}},
        {"final": {"abstention_reason": "no_relevant_documents", "top_k_before_rerank": 2}},
    ]
    out = p.get_multi_context(["a?", "b?"], standalone=True)
    assert out["chunks"] == [] and out["abstention_reason"] == "no_relevant_documents"


def test_scope_unavailable_reason_is_preserved_when_every_question_needs_scope():
    p = _pipeline()
    scope = {"final": {"abstention_reason": "academic_scope_unavailable", "top_k_before_rerank": 0}}
    p._search_many = lambda *a, **k: [scope, scope]
    out = p.get_multi_context(["my curriculum?", "my electives?"], standalone=True)
    assert out["abstention_reason"] == "academic_scope_unavailable"


def test_shared_token_budget_trims_every_question_evenly():
    """Grouped-by-question order would let question 1 consume the whole budget."""
    p = _pipeline()
    big = "word " * 150  # ~750 chars: only ~3 such docs fit the widened budget
    p._search_many = lambda *a, **k: [
        _search([_chunk(i, big, f"Q1 doc {i}") for i in (1, 2, 3, 4)]),
        _search([_chunk(i, big, f"Q2 doc {i}") for i in (11, 12, 13, 14)]),
    ]
    out = p.get_multi_context(["first?", "second?"], standalone=True)
    assert len(out["chunks"]) < 8, "budget should have trimmed something"
    assert all(e["in_context"] for e in out["per_question"])


def test_per_question_cap_limits_chunks_but_not_complete_list_questions(monkeypatch):
    monkeypatch.setattr(rp, "MULTI_PER_QUESTION_TOP_K", 2)
    p = _pipeline()
    many = [_chunk(i, f"row {i}") for i in range(1, 8)]
    p._search_many = lambda *a, **k: [
        _search(many, top_k=8), _search([_chunk(50 + i, f"x{i}") for i in range(5)], top_k=8),
    ]
    out = p.get_multi_context(["a?", "b?"], standalone=True)
    assert sum(1 for c in out["chunks"] if 1 in c["questions"]) == 2
    assert sum(1 for c in out["chunks"] if 2 in c["questions"]) == 2
    p._search_many = lambda *a, **k: [_search(many, top_k=15, complete_list=True), _search([_chunk(90)])]
    out = p.get_multi_context(["list all?", "b?"], standalone=True)
    assert sum(1 for c in out["chunks"] if 1 in c["questions"]) > 2


def test_search_many_isolates_a_failing_question_but_raises_if_all_fail():
    p = _pipeline()

    def fake_search(q, *a, **k):
        if q == "bad?":
            raise RuntimeError("qdrant hiccup")
        return _search([_chunk(1)])

    p._search_context = fake_search
    res = p._search_many(["good?", "bad?"], [], "public", None, None, [None, None], True)
    assert "search" in res[0] and "error" in res[1]

    p._search_context = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("down"))
    with pytest.raises(RuntimeError):
        p._search_many(["a?", "b?"], [], "public", None, None, [None, None], True)


def test_single_question_delegates_to_get_context_with_standalone_flag():
    p = _pipeline()
    seen = {}

    def fake_get_context(q, history, **kw):
        seen.update(q=q, **kw)
        return {"chunks": [_chunk(1)], "context": "<context></context>", "sources": []}

    p.get_context = fake_get_context
    out = p.get_multi_context(["only one?"], history=[{"role": "user", "content": "x"}], standalone=True)
    assert seen["q"] == "only one?" and seen["standalone"] is True
    assert out["per_question"][0]["in_context"] is True


def test_get_context_wrapper_returns_abstention_untouched():
    p = _pipeline()
    abstain = {"chunks": [], "abstention_reason": "no_relevant_documents"}
    p._search_context = lambda *a, **k: {"final": abstain}
    assert p.get_context("q") is abstain


# ── Context builder ─────────────────────────────────────────────────────

def test_builder_renders_question_tags_and_reports_included_chunks():
    builder = ContextBuilder()
    c1 = _chunk(1, "alpha text")
    c1["questions"] = [1, 3]
    built = builder.build([c1, _chunk(2, "beta text")], widen=True, n_questions=3)
    assert 'q="1,3"' in built["context"]
    assert built["included"] == [0, 1]


# ── Semester normalisation (planner int vs stored roman numeral) ────────

@pytest.mark.parametrize("value,expected", [
    ("III", {3}), (3, {3}), ("Semester 5", {5}), (["5", "6"], {5, 6}),
    ("3rd sem", {3}), ("Semester VIII", {8}), (None, set()), ("fourth", {4}), ("", set()),
])
def test_semester_numbers(value, expected):
    assert semester_numbers(value) == expected


def test_wrong_semester_curriculum_chunk_now_ranks_below_the_right_one(monkeypatch):
    """Before the fix 'III' != 3 penalised BOTH chunks equally."""
    monkeypatch.setenv("RERANKER_SERVICE_URL", "http://reranker.test")
    monkeypatch.setattr(
        "requests.Session.post",
        lambda self, *a, **k: SimpleNamespace(status_code=200, json=lambda: {"scores": [2.0, 2.0]}),
    )

    def cur(cid, sem):
        return {"id": cid, "metadata": {
            "text": f"Semester {sem} courses", "title": "Curriculum", "section_type": "curriculum",
            "semester": sem, "chunk_index": cid,
        }, "rrf_score": 0.02}

    plan = {"entities": {"semester": 3}, "retrieval_intent": "program_curriculum"}
    ranked = Reranker().rerank("What courses are in semester 3?", [cur(1, "V"), cur(2, "III")], plan)
    assert ranked[0]["metadata"]["semester"] == "III"
    assert ranked[0]["reranked_score"] > ranked[1]["reranked_score"]
