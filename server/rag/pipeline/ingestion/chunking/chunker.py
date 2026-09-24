import re
from transformers import AutoTokenizer
from config import (MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Fix H: how far back (in tokens) from a raw boundary we'll search for a
# sentence-ending punctuation to snap the cut to a clean sentence edge.
_SNAP_WINDOW = 30

# Fix J: words whose trailing "." is (almost always) part of an abbreviation,
# not a sentence end -- checked against the run of letters right before the
# period. Covers this corpus's common cases: degree abbreviations
# ("B.Tech.", "M.Tech.", "Ph.D."), titles ("Dr.", "Prof."), and "etc./e.g./i.e.".
# A single preceding letter ("B.", "M.", "U.") is always treated as an
# initial, not sentence-ending, without needing to be listed here.
_ABBREVIATION_FRAGMENTS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "vs", "etc", "eg", "ie",
    "no", "fig", "figs", "dept", "govt", "tech", "sc", "com", "phil", "ed",
    "llb", "llm", "co", "inc", "ltd", "vol", "pp", "ave", "st", "approx",
    "univ", "acad", "admn", "regd", "ph", "ug", "pg", "hons",
}
_WORD_BEFORE_RE = re.compile(r"([A-Za-z]+)\s*$")


def _is_abbreviation_period(text, period_pos):
    """True when the '.' at ``text[period_pos]`` is a decimal separator or
    part of an abbreviation, not a sentence end.

    Without this, "the fee is 8.5 lakhs" or "a B.Tech. degree" could be cut
    right after "8." or "B.", splitting a number or an abbreviation in two.
    Checked on the RAW source text (not a decoded token): the embedding
    tokenizer is uncased, so a decoded token had already lowercased and
    reshaped the very punctuation and letters this check depends on.
    """
    before, after = text[:period_pos], text[period_pos + 1:period_pos + 2]
    if before[-1:].isdigit() and after.isdigit():
        return True  # "8.5", "3.75"
    match = _WORD_BEFORE_RE.search(before)
    if not match:
        return False
    word = match.group(1)
    if len(word) == 1:
        return True  # initial: "B.", "M.", "U.", "K."
    return word.lower() in _ABBREVIATION_FRAGMENTS


def _snap_to_sentence_boundary(text, tokens, offsets, raw_end, window=_SNAP_WINDOW):
    # Starting from raw_end, scan backwards up to `window` tokens looking for
    # a token that ends a real sentence (., ?, !) -- not an abbreviation or a
    # decimal point (see _is_abbreviation_period).
    # Returns the adjusted end index (exclusive), or raw_end if none found.
    search_start = max(0, raw_end - window)
    for i in range(raw_end - 1, search_start - 1, -1):
        token_end_char = offsets[i][1]
        if token_end_char <= 0:
            continue
        last_char = text[token_end_char - 1]
        if last_char not in ".?!":
            continue
        if last_char == "." and _is_abbreviation_period(text, token_end_char - 1):
            continue
        return i + 1   # include this terminal token
    return raw_end


def _split_large_table(table_text, max_tokens=None):
    """Row-split a markdown table that alone exceeds one chunk.

    The header and separator row are repeated in every piece so each chunk
    stays a valid, self-contained table for embedding and reranking, and no
    row is duplicated across pieces. ``table_text`` must be a well-formed
    ``_TABLE_RE`` match: header row, separator row, then data rows.
    """
    if max_tokens is None:
        # Read CHUNK_SIZE at call time, not as a mutable-default baked in at
        # import time, so it always matches the module's current config.
        max_tokens = CHUNK_SIZE
    lines = table_text.strip("\n").split("\n")
    if len(lines) < 3:
        return [table_text.strip()]  # defensive: not well-formed, leave as-is
    header, separator, data_lines = lines[0], lines[1], lines[2:]
    overhead = len(tokenizer(header + "\n" + separator, add_special_tokens=False)["input_ids"])
    budget = max(1, max_tokens - overhead)

    pieces, group, group_tokens = [], [], 0
    for row in data_lines:
        if not row.strip():
            continue
        row_tokens = len(tokenizer(row, add_special_tokens=False)["input_ids"])
        if group and group_tokens + row_tokens > budget:
            pieces.append(group)
            group, group_tokens = [], 0
        group.append(row)
        group_tokens += row_tokens
    if group:
        pieces.append(group)
    if not pieces:
        return [table_text.strip()]
    return ["\n".join([header, separator, *rows]).strip() for rows in pieces]


_TABLE_RE = re.compile(r"(?m)^\|.*\|[\r\n]+\|[-:| ]+\|[\r\n]+(?:^\|.*\|[\r\n]*)+")

def split_section(text):
    # Split section into ~CHUNK_SIZE-token chunks with CHUNK_OVERLAP overlap.
    # Fix for Issue 5 (Table Chunking Fragmentation): Markdown tables are
    # detected via regex, and if a chunk's raw token boundary falls inside a
    # table, the boundary is pushed forward to the end of the table so it
    # remains intact in a single chunk (even if it exceeds soft token limits).
    # Boundaries outside tables are snapped to nearest sentence end.
    
    encoded = tokenizer(text, add_special_tokens=False, truncation=False, return_offsets_mapping=True)
    tokens = encoded.get("input_ids", [])
    offsets = encoded.get("offset_mapping", [])

    if len(tokens) <= CHUNK_SIZE:
        return [text]

    # Find character ranges of all Markdown tables, and how many tokens each
    # one is on its own -- needed up front to spot a table bigger than one
    # chunk (see the "oversized table" branch below).
    table_ranges = []
    table_token_counts = []
    for match in _TABLE_RE.finditer(text):
        table_ranges.append((match.start(), match.end()))
        table_token_counts.append(
            len(tokenizer(match.group(0), add_special_tokens=False)["input_ids"])
        )

    chunks = []
    start = 0

    while start < len(tokens):
        raw_end = start + CHUNK_SIZE

        # Fix I: a table bigger than one whole chunk is handled as its own
        # unit -- close whatever chunk precedes it right at the table's edge,
        # row-split the table (header/separator repeated per piece, see
        # _split_large_table), then resume normal chunking right after it.
        #
        # Without this, the "keep tables whole" branch below pushes the
        # boundary through to the end of ANY table regardless of size, so a
        # table bigger than one chunk was kept as a single chunk far past
        # bge's ~512-token embedding limit -- and process_corpus.py's
        # embed-limit retry (_enforce_embed_limit), which just calls
        # split_section again on the oversized chunk, could not shrink it
        # either: the whole retried text WAS the table, so the same branch
        # fired again and returned it unchanged.
        oversized_table = None
        if raw_end < len(tokens):
            char_pos = offsets[raw_end][0]
            for (t_start, t_end), t_tokens in zip(table_ranges, table_token_counts):
                if t_start < char_pos < t_end and t_tokens > CHUNK_SIZE:
                    oversized_table = (t_start, t_end)
                    break

        if oversized_table:
            t_start, t_end = oversized_table
            boundary = start
            while boundary < len(tokens) and offsets[boundary][0] < t_start:
                boundary += 1
            if boundary > start:
                char_start = offsets[start][0]
                char_end = offsets[boundary - 1][1]
                lead_text = text[char_start:char_end].strip()
                if lead_text:
                    chunks.append(lead_text)
            chunks.extend(_split_large_table(text[t_start:t_end]))
            resume = boundary
            while resume < len(tokens) and offsets[resume][0] < t_end:
                resume += 1
            start = resume if resume > start else start + 1  # always progress
            continue

        if raw_end < len(tokens):
            # Check if raw_end falls inside a (non-oversized) table
            char_pos = offsets[raw_end][0]
            in_table = False
            for t_start, t_end in table_ranges:
                if t_start < char_pos < t_end:
                    # Move raw_end forward to the end of this table
                    in_table = True
                    # Find first token whose start character is >= t_end
                    while raw_end < len(tokens) and offsets[raw_end][0] < t_end:
                        raw_end += 1
                    break

            if not in_table:
                # Snap forward boundary to a clean sentence end
                raw_end = _snap_to_sentence_boundary(text, tokens, offsets, raw_end)

            end = raw_end
        else:
            end = len(tokens)

        # Slice the original text by character offsets. Decoding the tokens
        # would go through the uncased BGE tokenizer: lowercase text, lost
        # line breaks, and "1,85,000" rendered as "1, 85, 000".
        char_start = offsets[start][0]
        char_end = offsets[end - 1][1] if end < len(tokens) else len(text)
        chunk_text = text[char_start:char_end].strip()
        chunks.append(chunk_text)

        if end >= len(tokens):
            break

        # Advance by (snapped_chunk_size - overlap); never go backwards
        advance = max(1, (end - start) - CHUNK_OVERLAP)
        start += advance

    return chunks
