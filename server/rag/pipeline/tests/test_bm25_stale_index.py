"""Regression test for rag_debug_report Stage: BM25, Bug 1:
'BM25 index not refreshed after new documents ingested'.

Before the fix, BM25Retriever built its index exactly once, in __init__.
Any documents ingested afterwards (metadata.json rewritten by the ingestion
pipeline) were invisible to BM25 search until the process was restarted,
silently diverging from Qdrant's up-to-date index.

The fix checks the metadata file's mtime on every retrieve() call and
rebuilds the in-memory index whenever it has changed.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.retrieval.bm25_retriever import BM25Retriever


def _write(path, chunks):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)


@pytest.fixture
def metadata_file():
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    _write(path, [{"text": "attendance policy overview", "title": "A", "chunk_id": "c1"}])
    yield path
    os.unlink(path)


def test_new_document_is_invisible_before_reingest(metadata_file):
    retriever = BM25Retriever(metadata_file)
    assert len(retriever.chunks) == 1


def test_retrieve_picks_up_documents_added_after_startup(metadata_file):
    retriever = BM25Retriever(metadata_file)
    assert len(retriever.chunks) == 1

    # Simulate a re-ingestion run rewriting metadata.json with a new chunk.
    time.sleep(1.05)  # ensure a distinct, detectable mtime
    _write(
        metadata_file,
        [
            {"text": "attendance policy overview", "title": "A", "chunk_id": "c1"},
            {"text": "scholarship eligibility criteria", "title": "B", "chunk_id": "c2"},
        ],
    )

    # No manual rebuild_index() call — retrieve() must self-heal.
    retriever.retrieve("scholarship", top_k=5)
    assert len(retriever.chunks) == 2, (
        "BM25 index must refresh from disk when metadata.json changes, "
        "without requiring a process restart"
    )


def test_no_unnecessary_rebuild_when_file_is_unchanged(metadata_file):
    retriever = BM25Retriever(metadata_file)
    first_bm25 = retriever.bm25
    retriever.retrieve("attendance", top_k=5)
    retriever.retrieve("attendance", top_k=5)
    # Same object reused: no needless rebuild churn on every query.
    assert retriever.bm25 is first_bm25
