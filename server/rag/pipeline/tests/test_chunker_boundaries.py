"""Chunker fixes: abbreviation/decimal-aware sentence snapping, and
row-splitting an oversized table instead of silently keeping it whole.

The real bge tokenizer needs network access to Hugging Face that this
sandbox does not have, so ``chunker.tokenizer`` is monkeypatched with a
small whitespace tokenizer for the integration-style tests below. The
abbreviation classifier itself is pure text logic and is tested directly,
with no tokenizer involved.
"""

import re
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

CHUNKING_DIR = Path(__file__).resolve().parents[1] / "ingestion" / "chunking"
if str(CHUNKING_DIR) not in sys.path:
    sys.path.insert(0, str(CHUNKING_DIR))

import transformers  # noqa: E402

with patch.object(transformers.AutoTokenizer, "from_pretrained", return_value=object()):
    import chunker  # noqa: E402


class WhitespaceTokenizer:
    """Splits on runs of non-whitespace, tracking exact character offsets.

    Stands in for the real fast tokenizer's ``__call__``/``decode`` subset
    that ``chunker.py`` uses, without needing model files.
    """

    _TOKEN_RE = re.compile(r"\S+")

    def __call__(self, text, add_special_tokens=False, truncation=False, return_offsets_mapping=False):
        offsets = [(m.start(), m.end()) for m in self._TOKEN_RE.finditer(text)]
        result = {"input_ids": list(range(len(offsets)))}
        if return_offsets_mapping:
            result["offset_mapping"] = offsets
        return result

    def decode(self, ids, skip_special_tokens=True):
        return ""  # unused: snapping now reads raw text, not decoded tokens


@pytest.fixture(autouse=True)
def _fake_tokenizer(monkeypatch):
    monkeypatch.setattr(chunker, "tokenizer", WhitespaceTokenizer())
    yield


def _table(n_rows, col2="Amount"):
    header = "| Semester | " + col2 + " |"
    sep = "|---|---|"
    rows = [f"| {i} | Row value number {i} here |" for i in range(1, n_rows + 1)]
    return "\n".join([header, sep, *rows])


# ── _is_abbreviation_period: pure logic, no tokenizer ────────────────────

@pytest.mark.parametrize("text,needle,offset,expected", [
    ("The fee is 8.5 lakhs.", "8.5", 1, True),               # decimal midpoint
    ("CGPA required is 3.75 or above.", "3.75", 1, True),    # decimal midpoint
    ("Admission requires a B.Tech. degree.", "B.", 1, True),          # initial
    ("Admission requires a B.Tech. degree.", "Tech.", 4, True),       # abbreviation word
    ("Holders of a Ph.D. degree get priority.", "Ph.", 2, True),      # "ph" fragment
    ("Holders of a Ph.D. degree get priority.", "D.", 1, True),       # single-letter initial
    ("Contact Dr. Mehta for details.", "Dr.", 2, True),
    ("Bring documents, etc. before the deadline.", "etc.", 3, True),
    ("This is a complete sentence.", "sentence.", 8, False),  # real sentence end
])
def test_is_abbreviation_period(text, needle, offset, expected):
    pos = text.index(needle) + offset
    assert text[pos] == "."
    assert chunker._is_abbreviation_period(text, pos) is expected


def test_real_sentence_end_after_a_number_is_not_treated_as_decimal():
    text = "The total is 500. Admissions close soon."
    period_pos = text.index("500.") + 3
    assert chunker._is_abbreviation_period(text, period_pos) is False


def test_single_letter_initial_mid_name_is_treated_as_abbreviation():
    text = "Contact A. K. Sharma for queries."
    pos = text.index("A.") + 1
    assert chunker._is_abbreviation_period(text, pos) is True


# ── _snap_to_sentence_boundary: raw-text based, abbreviation-aware ───────

def _encode(text):
    enc = chunker.tokenizer(text, return_offsets_mapping=True)
    return enc["input_ids"], enc["offset_mapping"]


def test_snap_skips_a_decimal_point_and_finds_the_real_sentence_end():
    text = "The tuition fee is 8.5 lakhs per year for this programme now offered."
    tokens, offsets = _encode(text)
    # Force raw_end to land just after "8.5" (an old bug would snap here).
    raw_end = next(i for i, (s, e) in enumerate(offsets) if text[s:e] == "8.5") + 1
    snapped = chunker._snap_to_sentence_boundary(text, tokens, offsets, raw_end, window=5)
    assert snapped == raw_end  # no real sentence end nearby -> unchanged


def test_snap_skips_an_abbreviation_and_reaches_further_back_for_the_real_one():
    # raw_end sits right after "B.Tech."; the nearest REAL sentence end is
    # earlier still, at "here." A pre-fix snap would have cut right after the
    # abbreviation's period, splitting "B.Tech." from the rest of its name.
    text = "This is one sentence right here. A student needs a B.Tech. degree today."
    tokens, offsets = _encode(text)
    raw_end = next(i for i, (s, e) in enumerate(offsets) if text[s:e] == "B.Tech.") + 1
    snapped = chunker._snap_to_sentence_boundary(text, tokens, offsets, raw_end, window=20)
    snapped_text = text[offsets[0][0]:offsets[snapped - 1][1]]
    assert snapped_text == "This is one sentence right here."
    assert snapped < raw_end  # boundary moved earlier, past the abbreviation


def test_snap_still_finds_a_genuine_sentence_end_immediately():
    text = "This is one sentence. This is the next one right here today for testing."
    tokens, offsets = _encode(text)
    raw_end = next(i for i, (s, e) in enumerate(offsets) if text[s:e] == "sentence.") + 1
    snapped = chunker._snap_to_sentence_boundary(text, tokens, offsets, raw_end, window=5)
    assert snapped == raw_end


# ── _split_large_table: header/separator repeated, rows never duplicated ─

def test_split_large_table_repeats_header_and_covers_every_row_once():
    monkeypatch_size = 12
    chunker.CHUNK_SIZE = monkeypatch_size  # simple module attr for this test
    try:
        table = _table(20)
        pieces = chunker._split_large_table(table, max_tokens=monkeypatch_size)
        assert len(pieces) > 1
        for piece in pieces:
            lines = piece.split("\n")
            assert lines[0] == "| Semester | Amount |"
            assert lines[1] == "|---|---|"
        all_rows = [row for piece in pieces for row in piece.split("\n")[2:]]
        assert len(all_rows) == 20 and len(set(all_rows)) == 20  # no duplicates, none dropped
        for i in range(1, 21):
            assert any(f"| {i} |" in row for row in all_rows)
    finally:
        chunker.CHUNK_SIZE = 256


def test_split_large_table_reads_current_chunk_size_not_an_import_time_default(monkeypatch):
    """max_tokens=None must read chunker.CHUNK_SIZE at call time."""
    monkeypatch.setattr(chunker, "CHUNK_SIZE", 15)
    pieces = chunker._split_large_table(_table(20))
    assert len(pieces) > 1


def test_malformed_table_text_is_returned_unsplit():
    assert chunker._split_large_table("not a table") == ["not a table"]


# ── split_section: the oversized-table branch end to end ─────────────────

@pytest.fixture
def _small_chunks(monkeypatch):
    monkeypatch.setattr(chunker, "CHUNK_SIZE", 25)
    monkeypatch.setattr(chunker, "CHUNK_OVERLAP", 4)


def test_oversized_table_is_row_split_with_header_in_every_piece(_small_chunks):
    text = "Fee structure for the programme is given below.\n\n" + _table(15)
    chunks = chunker.split_section(text)
    table_chunks = [c for c in chunks if c.startswith("| Semester")]
    assert len(table_chunks) > 1, "the table alone exceeds CHUNK_SIZE and must be split"
    for c in table_chunks:
        assert c.split("\n")[0] == "| Semester | Amount |"
    all_rows = [row for c in table_chunks for row in c.split("\n")[2:]]
    assert len(all_rows) == 15 == len(set(all_rows))
    assert any("Fee structure" in c for c in chunks)  # lead-in prose preserved


def test_small_table_still_kept_whole_unchanged_from_before(_small_chunks):
    text = "Intro line here today about the course now offered widely.\n\n" + _table(2)
    chunks = chunker.split_section(text)
    table_bearing = [c for c in chunks if "| Semester | Amount |" in c]
    assert len(table_bearing) == 1, "a table that fits in one chunk must not be row-split"
    for row in _table(2).split("\n")[2:]:
        assert row in table_bearing[0]


def test_enforce_embed_limit_bug_is_fixed_oversized_table_now_actually_shrinks(monkeypatch):
    """Reproduces the pre-fix bug: process_corpus._enforce_embed_limit calls
    split_section(chunk) again on an over-limit chunk. When that chunk WAS
    the whole table, the old code re-detected "boundary falls inside a
    table" and pushed straight through to the end again, returning the same
    oversized chunk unchanged -- infinite non-progress. It must now shrink."""
    monkeypatch.setattr(chunker, "CHUNK_SIZE", 20)
    table_text = _table(25)
    tokens_before = len(chunker.tokenizer(table_text)["input_ids"])
    assert tokens_before > chunker.CHUNK_SIZE
    retried = chunker.split_section(table_text)
    assert len(retried) > 1
    for piece in retried:
        assert len(chunker.tokenizer(piece)["input_ids"]) <= tokens_before


def test_split_section_short_text_unaffected():
    assert chunker.split_section("Short text.") == ["Short text."]
