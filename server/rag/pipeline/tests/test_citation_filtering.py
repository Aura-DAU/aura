# Tests for citation-filtered sources.
#
# The bug this guards: every retrieved chunk was returned as a source pill
# regardless of whether the answer cited it. An ungrounded answer ("the
# retrieved documents do not provide information about him") still rendered a
# source card, so a hallucination arrived dressed as a grounded fact.
#
# Two halves:
#   ContextBuilder      — builds the doc_id → source-index map.
#   filter_sources_*    — narrows sources to the ids the answer actually cited.

import sys
from pathlib import Path

RAG_DIR = Path(__file__).resolve().parent.parent.parent  # server/rag
for p in (str(RAG_DIR),):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.generation.answer_generator import (
    extract_cited_ids,
    filter_sources_by_citations,
)


def _chunk(title, url=None, path=None, text="body text"):
    return {
        "metadata": {
            "title": title,
            "url": url,
            "relative_path": path,
            "text": text,
        }
    }


# ---------------------------------------------------------------------------
# ContextBuilder.citation_map
# ---------------------------------------------------------------------------

def test_citation_map_is_identity_when_no_duplicates():
    built = ContextBuilder().build([
        _chunk("A", url="https://dau.ac.in/a"),
        _chunk("B", url="https://dau.ac.in/b"),
        _chunk("C", url="https://dau.ac.in/c"),
    ])
    assert len(built["sources"]) == 3
    assert built["citation_map"] == {1: 0, 2: 1, 3: 2}


def test_citation_map_collapses_duplicate_sources():
    # Two chunks from the same document dedup to one source entry, but each
    # still gets its own <doc id>. This is exactly the case where mapping a
    # cited id to sources[id - 1] would return the wrong document.
    built = ContextBuilder().build([
        _chunk("A", url="https://dau.ac.in/a", text="first chunk"),
        _chunk("A", url="https://dau.ac.in/a", text="second chunk"),
        _chunk("B", url="https://dau.ac.in/b"),
    ])
    assert len(built["sources"]) == 2
    assert built["citation_map"] == {1: 0, 2: 0, 3: 1}

    # Citing doc 3 must yield source B, not the out-of-range positional guess.
    kept = filter_sources_by_citations(
        built["sources"], built["citation_map"], "Answer.\n\n[Sources: 3]"
    )
    assert [s["title"] for s in kept] == ["B"]


def test_citation_map_falls_back_to_path_then_title():
    # Internal markdown has no public URL; it must still be citeable.
    built = ContextBuilder().build([
        _chunk("A", path="data/policies/a.md"),
        _chunk("B"),
    ])
    assert len(built["sources"]) == 2
    assert built["citation_map"] == {1: 0, 2: 1}


# ---------------------------------------------------------------------------
# extract_cited_ids
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "answer,expected",
    [
        ("Fees are 2 lakh.\n\n[Sources: 1]", {1}),
        ("Text.\n\n[Sources: 1, 3, 7]", {1, 3, 7}),
        ("Text.\n\n[Sources:2,4]", {2, 4}),
        ("No citations at all.", set()),
        ("", set()),
    ],
)
def test_extract_cited_ids(answer, expected):
    assert extract_cited_ids(answer) == expected


# ---------------------------------------------------------------------------
# filter_sources_by_citations
# ---------------------------------------------------------------------------

SOURCES = [{"title": "A"}, {"title": "B"}, {"title": "C"}]
CMAP = {1: 0, 2: 1, 3: 2}


def test_uncited_answer_returns_no_sources():
    # The reported bug: an answer that explicitly says the documents contain
    # nothing must not carry a source pill.
    answer = (
        "Donald Trump is a former U.S. president. The retrieved documents do "
        "not provide information about him."
    )
    assert filter_sources_by_citations(SOURCES, CMAP, answer) == []


def test_only_cited_sources_are_kept():
    kept = filter_sources_by_citations(SOURCES, CMAP, "Text.\n\n[Sources: 1, 3]")
    assert [s["title"] for s in kept] == ["A", "C"]


def test_source_order_is_preserved():
    # Retrieval rank order must survive filtering — the top-ranked source
    # stays first regardless of the order ids appear in the marker.
    kept = filter_sources_by_citations(SOURCES, CMAP, "Text.\n\n[Sources: 3, 1]")
    assert [s["title"] for s in kept] == ["A", "C"]


def test_out_of_range_citation_is_ignored():
    # A model that invents [9] must not crash the turn or leak a wrong pill.
    kept = filter_sources_by_citations(SOURCES, CMAP, "Text.\n\n[Sources: 1, 9]")
    assert [s["title"] for s in kept] == ["A"]


def test_empty_sources_short_circuits():
    assert filter_sources_by_citations([], {}, "Text.\n\n[Sources: 1]") == []


def test_missing_citation_map_falls_back_to_position():
    # ERP-only turns and older callers pass no map; positional resolution is
    # correct there because no dedup has occurred.
    kept = filter_sources_by_citations(SOURCES, {}, "Text.\n\n[Sources: 2]")
    assert [s["title"] for s in kept] == ["B"]
