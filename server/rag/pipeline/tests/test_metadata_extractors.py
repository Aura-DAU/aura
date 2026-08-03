"""Regression tests for resolve_document_academic_year's bare-year fallback.

Fix YEAR-UB1: `\\b(20\\d{2})\\b` never matches a year embedded in a
snake_case filename ("..._autumn_2025_page_7.md") because `_` counts as a
\\w character, so there is no word-boundary transition between "_" and
"2025". That silently skipped this whole extraction step for the majority
of this corpus's filenames (which are snake_case) and let resolution fall
through to `scraped_date` — the ingest date, not the document's real
year — mistagging dozens of "Autumn 2025" course-policy documents as 2026
purely because they happened to be scraped in 2026.

A spot-check across the full corpus (1,437 markdown files) found this
pattern in at least 20 documents before the fix; see conversation history
for the reproduction script.
"""

import sys
from pathlib import Path

# Placed in server/rag/pipeline/tests/ alongside the rest of the suite
# (test_ingestion_metadata.py uses the same bootstrap) so `pytest pipeline/tests`
# in CI discovers it — metadata_extractors.py itself lives one level deeper,
chunking_dir = Path(__file__).resolve().parent.parent / "ingestion" / "chunking"
sys.path.insert(0, str(chunking_dir))

from metadata_extractors import resolve_document_academic_year


def test_underscore_separated_filename_year_is_detected():
    """The bug's exact reproduction case: no frontmatter year, only a
    snake_case filename with the year buried between underscores."""
    metadata = {
        "title": "Introduction to ICT",
        "scraped_date": "2026-06-08",
    }
    path = Path("course_policy_it101_introduction_to_ict_autumn_2025_page_7.md")
    document_year, academic_year = resolve_document_academic_year(metadata, path, "")
    assert document_year == 2025
    assert academic_year is None


def test_scraped_date_only_wins_when_no_year_anywhere_else():
    """scraped_date must still be the last-resort fallback when the
    filename/title genuinely carry no year at all."""
    metadata = {"title": "Course File", "scraped_date": "2026-06-08"}
    path = Path("course_policy_unknown_page_7.md")
    document_year, _ = resolve_document_academic_year(metadata, path, "")
    assert document_year == 2026


def test_underscore_separated_year_does_not_false_positive_on_five_digits():
    """Digit-adjacency lookaround must reject a 5-digit run, not just widen
    to match anything containing 4 digits."""
    metadata = {"title": "Report", "scraped_date": "2026-06-08"}
    path = Path("archive_id_120259_summary.md")
    document_year, _ = resolve_document_academic_year(metadata, path, "")
    # "20259" contains no valid standalone 20xx year adjacent to non-digits,
    # so this must NOT resolve to 2025 (or any digit substring of "120259");
    # it should fall through to scraped_date.
    assert document_year == 2026


def test_academic_year_label_still_beats_bare_year_in_filename():
    """Regression guard: the fix must not disturb priority ordering — an
    explicit YYYY-YY academic-year label in the filename still wins over
    (and agrees with) the bare-year fallback."""
    metadata = {"title": "Club Committee C_DCs Information 2025-26"}
    path = Path("sbg_club_committee_c_dcs_information_2025_26.md")
    document_year, academic_year = resolve_document_academic_year(metadata, path, "")
    assert document_year == 2025
    assert academic_year == "2025-26"


def test_hyphenated_filename_year_still_detected():
    """Non-underscore separators (hyphens) were never broken; guard against
    a fix that accidentally narrows matching instead of widening it."""
    metadata = {"title": "Course File"}
    path = Path("course-policy-autumn-2025-page-7.md")
    document_year, _ = resolve_document_academic_year(metadata, path, "")
    assert document_year == 2025
