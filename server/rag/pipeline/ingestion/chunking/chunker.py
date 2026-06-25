from transformers import AutoTokenizer
from config import (MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Fix H: how far back (in tokens) from a raw boundary we'll search for a
# sentence-ending punctuation to snap the cut to a clean sentence edge.
_SNAP_WINDOW = 30


def _snap_to_sentence_boundary(tokens, raw_end, window=_SNAP_WINDOW):
    """
    Starting from raw_end, scan backwards up to `window` tokens looking for
    a token whose decoded text ends a sentence (., ?, !).
    Returns the adjusted end index (exclusive), or raw_end if none found.
    """
    search_start = max(0, raw_end - window)
    for i in range(raw_end - 1, search_start - 1, -1):
        word = tokenizer.decode([tokens[i]], skip_special_tokens=True).strip()
        if word and word[-1] in ".?!":
            return i + 1   # include this terminal token
    return raw_end


def split_section(text):
    """
    Split section into ~CHUNK_SIZE-token chunks with CHUNK_OVERLAP overlap.

    Fix H: chunk boundaries are snapped to the nearest sentence end within
    _SNAP_WINDOW tokens so that chunks don't start/end on broken words.
    """

    tokens = tokenizer.encode(text, add_special_tokens=False, truncation=False)

    if len(tokens) <= CHUNK_SIZE:
        return [text]

    chunks = []

    start = 0

    while start < len(tokens):
        raw_end = start + CHUNK_SIZE

        if raw_end < len(tokens):
            # Snap forward boundary to a clean sentence end
            end = _snap_to_sentence_boundary(tokens, raw_end)
        else:
            end = len(tokens)

        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)

        # Advance by (snapped_chunk_size - overlap); never go backwards
        advance = max(1, (end - start) - CHUNK_OVERLAP)
        start += advance

    return chunks