import re
from transformers import AutoTokenizer
from config import (MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Fix H: how far back (in tokens) from a raw boundary we'll search for a
# sentence-ending punctuation to snap the cut to a clean sentence edge.
_SNAP_WINDOW = 30


def _snap_to_sentence_boundary(tokens, raw_end, window=_SNAP_WINDOW):
    # Starting from raw_end, scan backwards up to `window` tokens looking for
    # a token whose decoded text ends a sentence (., ?, !).
    # Returns the adjusted end index (exclusive), or raw_end if none found.
    search_start = max(0, raw_end - window)
    for i in range(raw_end - 1, search_start - 1, -1):
        word = tokenizer.decode([tokens[i]], skip_special_tokens=True).strip()
        if word and word[-1] in ".?!":
            return i + 1   # include this terminal token
    return raw_end


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

    # Find character ranges of all Markdown tables
    table_ranges = []
    for match in _TABLE_RE.finditer(text):
        table_ranges.append((match.start(), match.end()))

    chunks = []
    start = 0

    while start < len(tokens):
        raw_end = start + CHUNK_SIZE

        if raw_end < len(tokens):
            # Check if raw_end falls inside a table
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
                raw_end = _snap_to_sentence_boundary(tokens, raw_end)
            
            end = raw_end
        else:
            end = len(tokens)

        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

        if end >= len(tokens):
            break

        # Advance by (snapped_chunk_size - overlap); never go backwards
        advance = max(1, (end - start) - CHUNK_OVERLAP)
        start += advance

    return chunks
