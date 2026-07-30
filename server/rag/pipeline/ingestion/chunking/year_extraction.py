"""
Shared academic/calendar year extraction logic.

Pulled out of process_corpus.py into its own zero-third-party-dependency
module so it can be reused (e.g. by mark_document_years.py) without pulling
in process_corpus.py's heavy chunking dependencies (transformers, etc.).
Keep this as the single source of truth — reranker.py and context_builder.py
intentionally keep their own lightweight inline copies for the retrieval-time
path (no import across service boundaries there), but any change to the year
regex/convention should be mirrored in those two spots as well.
"""
import re


def extract_academic_or_calendar_year(text):
    if not text:
        return None
    text_str = str(text)
    # 1. 4-digit academic year range (e.g. 2024-25, 2024_25, 2024 25, 2024-2025)
    m4 = re.search(r"(?<!\d)(20\d{2})[\s\-_\u2013](\d{2}|\d{4})(?!\d)", text_str)
    if m4:
        y1_int = int(m4.group(1))
        y2_int = int(m4.group(2)[-2:])
        if y2_int == (y1_int + 1) % 100:
            return f"{y1_int}-{y2_int:02d}"

    # 2. 2-digit academic year range (e.g. 24_25, 24-25, 25_26, 25-26, 26_27, 26-27)
    m2 = re.search(r"(?<!\d)(2\d)[\s\-_\u2013](\d{2})(?!\d)", text_str)
    if m2:
        y1 = int(m2.group(1))
        y2 = int(m2.group(2))
        if 20 <= y1 <= 35 and y2 == (y1 + 1) % 100:
            return f"20{y1:02d}-{y2:02d}"

    # 3. Bare season/term + 2-digit (or 4-digit) year with NO range given, e.g.
    # "Winter25", "Autumn 2025", "Winter_24". This corpus pairs "Autumn NN"
    # and "Winter NN" under the same NN (Winter directly follows Autumn of the
    # same numbered academic year), so both map to academic year "NN-(NN+1)".
    m3 = re.search(
        r"(?i)\b(?:autumn|winter|monsoon|spring|summer)[\s_-]?(?:20)?(\d{2})\b(?![\s_-]?\d)",
        text_str,
    )
    if m3:
        y1 = int(m3.group(1))
        if 20 <= y1 <= 35:
            return f"20{y1:02d}-{(y1 + 1) % 100:02d}"

    # 4. 4-digit single calendar year (e.g. 2025)
    m1 = re.search(r"(?<!\d)(20\d{2})(?!\d)", text_str)
    if m1:
        try:
            return int(m1.group(1))
        except ValueError:
            return m1.group(1)

    return None
