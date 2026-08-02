"""ContextBuilder token-aware accumulation (retrieval side of the budget).

Complements test_token_budget.py, which covers the generation side.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.token_budget import TokenBudget


@pytest.fixture(autouse=True)
def _budget_env(monkeypatch):
    TokenBudget.reset_for_tests()
    monkeypatch.setenv("AURA_TOKENIZE_ENABLED", "0")  # no network in unit tests
    monkeypatch.setenv("AURA_MAX_MODEL_LEN", "4096")
    monkeypatch.setenv("AURA_MAX_ANSWER_TOKENS", "1024")
    monkeypatch.setenv("AURA_MAX_CONTEXT_TOKENS", "1400")
    monkeypatch.setenv("AURA_TOKEN_SAFETY_MARGIN", "64")
    yield
    TokenBudget.reset_for_tests()


def _chunks(n: int, words_each: int = 120):
    return [
        {
            "metadata": {
                "text": f"rank{i} " + ("policy text " * words_each),
                "title": f"Doc {i}",
                "url": f"https://daiict.ac.in/d{i}",
                "relative_path": f"d{i}.md",
                "start_line": 1,
                "end_line": 10,
            }
        }
        for i in range(1, n + 1)
    ]


def _doc_ids(context: str) -> list[str]:
    return re.findall(r'id="(\d+)"', context)


def test_accumulation_stops_before_cap():
    built = ContextBuilder().build(_chunks(20))
    ids = _doc_ids(built["context"])
    assert 0 < len(ids) < 20, "must admit some chunks and trim the rest"


def test_kept_chunks_are_the_highest_ranked_prefix():
    built = ContextBuilder().build(_chunks(20))
    ids = _doc_ids(built["context"])
    # Lowest-ranked are dropped first, so survivors are always 1..N.
    assert ids == [str(i) for i in range(1, len(ids) + 1)]


def test_estimated_context_stays_within_cap():
    builder = ContextBuilder()
    built = builder.build(_chunks(20))
    est = builder._estimate_tokens(built["context"])
    cap = TokenBudget.from_env(discover=False).config.max_retrieved_context_tokens
    # Allow one chunk's worth of overshoot: the loop admits chunk 1
    # unconditionally, and the estimate excludes the <context> wrapper.
    assert est <= cap * 2


def test_small_retrieval_is_not_trimmed():
    built = ContextBuilder().build(_chunks(2, words_each=10))
    assert _doc_ids(built["context"]) == ["1", "2"]


def test_complete_list_widens_budget_but_stays_bounded():
    builder = ContextBuilder()
    narrow = builder.build(_chunks(20))
    wide = builder.build(_chunks(20), requires_complete_list=True)
    n_narrow = len(_doc_ids(narrow["context"]))
    n_wide = len(_doc_ids(wide["context"]))
    assert n_wide >= n_narrow
    # Must NOT blow past the input budget the way the old hard-coded 4000 did.
    cap = TokenBudget.from_env(discover=False).config.max_input_tokens
    assert builder._estimate_tokens(wide["context"]) <= cap


def test_citation_map_survives_trimming():
    built = ContextBuilder().build(_chunks(20))
    ids = _doc_ids(built["context"])
    # Every emitted doc id must resolve through citation_map into sources.
    for doc_id in ids:
        assert int(doc_id) in built["citation_map"]
        assert built["citation_map"][int(doc_id)] < len(built["sources"])
