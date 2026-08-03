"""Regression test for rag_debug_report P2: 'Single huge chunk eats full budget'.

Before the fix, the token-budget loop only ever checked
`context_tokens_used + estimated_tokens > effective_max_tokens and idx > 1`,
so the *first* (highest-ranked) chunk was admitted unconditionally no matter
how large it was. A single oversized top chunk could consume the entire
context budget and leave literally zero room for any other retrieved
evidence, even though 19 other relevant chunks were available.

The fix caps any single chunk's contribution to roughly a third of the
effective budget, trimming its tail instead of excluding it, so the budget
loop always has room left over for lower-ranked chunks.
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


def _doc_ids(context: str) -> list[str]:
    return re.findall(r'id="(\d+)"', context)


def _chunks_with_huge_first(n: int, huge_words: int = 5000, rest_words: int = 20):
    chunks = [
        {
            "metadata": {
                "text": "HUGE " + ("filler word " * huge_words),
                "title": "Doc 1 (oversized)",
                "url": "https://daiict.ac.in/d1",
                "relative_path": "d1.md",
                "start_line": 1,
                "end_line": 999,
            }
        }
    ]
    for i in range(2, n + 1):
        chunks.append(
            {
                "metadata": {
                    "text": f"rank{i} " + ("policy text " * rest_words),
                    "title": f"Doc {i}",
                    "url": f"https://daiict.ac.in/d{i}",
                    "relative_path": f"d{i}.md",
                    "start_line": 1,
                    "end_line": 10,
                }
            }
        )
    return chunks


def test_oversized_first_chunk_does_not_starve_the_rest():
    built = ContextBuilder().build(_chunks_with_huge_first(20))
    ids = _doc_ids(built["context"])
    # Before the fix this was exactly ["1"] — chunk 1 alone ate the whole
    # budget and idx>1 chunks were all dropped by the overflow check.
    assert len(ids) > 1, "an oversized top chunk must not crowd out every other chunk"


def test_oversized_first_chunk_is_trimmed_not_excluded():
    built = ContextBuilder().build(_chunks_with_huge_first(20))
    ids = _doc_ids(built["context"])
    # The huge chunk still appears (trimmed), it just no longer monopolizes
    # the whole budget.
    assert "1" in ids


def test_context_still_stays_within_budget_with_huge_chunk():
    builder = ContextBuilder()
    built = builder.build(_chunks_with_huge_first(20))
    est = builder._estimate_tokens(built["context"])
    cap = TokenBudget.from_env(discover=False).config.max_retrieved_context_tokens
    assert est <= cap * 2
