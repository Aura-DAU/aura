"""
chunk_quality.py — Chunk quality validation and duplicate detection.

Two independent, composable checks, both operating on the chunk dicts
produced by process_markdown_file() (see process_corpus.py):

1. is_low_quality_chunk() — catches empty/near-empty/low-information
   chunks before they're ever written to metadata.json or embedded.
   Previously nothing filtered these out: a section with only a table
   caption, a stray heading with no body text, or an accidental
   whitespace-only split could produce a chunk that contributes nothing
   to retrieval but still costs an embedding call and a Qdrant point.

2. annotate_duplicate_chunks() — flags chunks whose *normalized content*
   (not chunk_id — two different files can produce byte-identical prose,
   e.g. a shared disclaimer or boilerplate section) already appears
   elsewhere in the corpus. Duplicates are NOT deleted — a chunk is still
   valid to retrieve from its own document's context — they're annotated
   with `is_duplicate` / `duplicate_of_chunk_id` instead.

   Scope note: this only flags duplicates today; it does NOT yet skip
   re-embedding a flagged duplicate or reuse the canonical chunk's vector.
   Doing that safely requires touching the embeddings.npy / metadata.json
   index-alignment logic in sync_incremental.py (row i of one must always
   correspond exactly to entry i of the other) — deliberately left as a
   follow-up with real test data rather than implemented blind here. What
   this DOES give you now: a `duplicate_of_chunk_id` field on every chunk
   record, which retrieval-time result post-processing can use to collapse
   near-identical repeats in a result list instead of showing the same
   paragraph five times from five different pages.
"""

from __future__ import annotations

import hashlib
import re
from typing import Optional

# A chunk shorter than this many non-whitespace characters after stripping
# markdown table/heading noise carries essentially no retrievable signal.
# Chosen well below the smallest legitimate chunk we've seen in the corpus
# (e.g. a one-line "Office Hours: Mon 2-4pm" chunk is ~25 chars) so this
# only catches genuinely empty/junk splits, not terse-but-real content.
MIN_CHUNK_CHARS = 15


def _normalize_for_comparison(text: str) -> str:
    """Same normalization family as chunk_id_generator's content hash, but
    also strips the H1/H2/H3/Faculty-Name prefix lines process_corpus.py
    prepends to every chunk — two chunks with genuinely identical body
    content but different section headers should NOT be flagged as
    duplicates of each other (the header IS the differentiating content)."""
    if not text:
        return ""
    lines = text.replace("\r\n", "\n").strip().split("\n")
    body_lines = [
        ln for ln in lines
        if not re.match(r"^(H[123]:|Faculty Name:|Document Title:)\s", ln)
    ]
    collapsed = " ".join(" ".join(body_lines).split())
    return collapsed.lower()


def is_low_quality_chunk(chunk_text: str) -> bool:
    """True if this chunk has too little substantive content to be worth
    storing/embedding/retrieving."""
    normalized = _normalize_for_comparison(chunk_text)
    # Strip residual markdown table pipes/dashes and punctuation-only noise
    # before measuring length, so a chunk that's purely "| --- | --- |"
    # (a malformed table fragment) doesn't count as 20 "characters" of
    # content.
    alnum_only = re.sub(r"[^a-z0-9]", "", normalized)
    return len(alnum_only) < MIN_CHUNK_CHARS


def compute_content_hash(chunk_text: str) -> str:
    normalized = _normalize_for_comparison(chunk_text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def annotate_duplicate_chunks(
    chunks: list[dict],
    existing_hashes: Optional[dict[str, str]] = None,
) -> tuple[list[dict], int]:
    """Marks chunks whose content already appeared earlier.

    `chunks` is scanned in order; the FIRST chunk with a given content hash
    is the canonical one. `existing_hashes` (content_hash -> chunk_id) lets
    callers doing incremental re-indexing (sync_incremental.py) check new
    chunks against everything already in the index, not just against each
    other.

    Returns (annotated_chunks, duplicate_count). Chunks are never dropped
    here — callers decide what to do with is_duplicate (e.g. skip
    embedding, or just carry the flag through to metadata for later
    analysis).
    """
    seen: dict[str, str] = dict(existing_hashes or {})
    duplicate_count = 0
    annotated = []

    for chunk in chunks:
        content_hash = compute_content_hash(chunk.get("text", ""))
        canonical_id = seen.get(content_hash)

        chunk = dict(chunk)
        if canonical_id and canonical_id != chunk.get("chunk_id"):
            chunk["is_duplicate"] = True
            chunk["duplicate_of_chunk_id"] = canonical_id
            duplicate_count += 1
        else:
            chunk["is_duplicate"] = False
            seen.setdefault(content_hash, chunk.get("chunk_id"))

        annotated.append(chunk)

    return annotated, duplicate_count
