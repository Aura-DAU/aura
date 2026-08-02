"""Unit tests for reranker.extract_latest_year.

extract_latest_year supplies the document version-year that drives the
reranker's temporal_boost (recency). It must key off authoritative fields
(document_year, title, section headings) only — incidental or future dates in
the free-text chunk body (graduation years, deadlines, validity periods) are
NOT the document's version and must not be read as recency, or a stale chunk
that merely mentions a recent/future year outranks the actually-current one.
"""

from pipeline.retrieval.reranker import extract_latest_year


def test_structured_document_year_takes_priority():
    assert extract_latest_year({"document_year": "2026", "text": "founded in 2019"}) == 2026


def test_title_academic_year_detected():
    assert extract_latest_year({"title": "Fee Structure 2025-26"}) == 2025


def test_full_year_range_in_title():
    assert extract_latest_year({"title": "Curriculum 2025-2026"}) == 2025


def test_section_heading_year_detected():
    assert extract_latest_year({"h2": "Academic Calendar 2026-27"}) == 2026


def test_latest_year_within_a_field_wins():
    assert extract_latest_year({"title": "Roster 2019 revised 2024"}) == 2024


def test_incidental_future_body_year_is_ignored():
    """Regression guard: a future graduation year in the body must not be read
    as the document's version year (the reason body text is no longer scanned)."""
    md = {
        "title": "Academic Regulations",
        "text": "Students admitted in 2019 will graduate in 2028.",
    }
    assert extract_latest_year(md) is None


def test_no_year_anywhere_returns_none():
    assert extract_latest_year({"title": "Hostel Rules", "text": "No years mentioned here."}) is None
