import sys
from pathlib import Path

# Add chunking directory to path so local imports resolve correctly
chunking_dir = Path(__file__).resolve().parent.parent / "ingestion" / "chunking"
sys.path.insert(0, str(chunking_dir))

from section_extracter import extract_sections
from process_corpus import find_line_range_in_file, process_markdown_file
from metadata_extractors import extract_academic_applicability

def test_extract_sections_line_ranges():
    markdown = """# Title
Some text on line 2.
Some text on line 3.

## Heading 2
Text under heading 2 on line 6."""
    sections = extract_sections(markdown, start_line_offset=1)
    
    assert len(sections) == 2
    
    # Section 1 starts at H1 (line 1) and ends before H2 (line 4)
    assert sections[0]["h1"] == "Title"
    assert sections[0]["start_line"] == 1
    assert sections[0]["end_line"] == 4
    
    # Section 2 starts at H2 (line 5) and ends at end of file (line 6)
    assert sections[1]["h2"] == "Heading 2"
    assert sections[1]["start_line"] == 5
    assert sections[1]["end_line"] == 6

def test_find_line_range_in_file():
    file_lines = [
        "---",
        "title: Policy Document",
        "---",
        "# Policy details",
        "This is a policy document details paragraph.",
        "It contains specific rules for registration.",
        "## Section 2",
        "More details here."
    ]
    
    chunk_text = "H1: Policy details\n\nIt contains specific rules for registration."
    
    start_line, end_line = find_line_range_in_file(
        chunk_text,
        file_lines,
        section_start=4,
        section_end=8
    )
    
    # "It contains specific rules for registration" is line 6 (1-indexed)
    assert start_line == 6
    assert end_line == 6

def test_process_markdown_file_metadata(tmp_path):
    # Create the required "data" directory structure in the temp path
    data_dir = tmp_path / "data" / "academics"
    data_dir.mkdir(parents=True, exist_ok=True)
    temp_file = data_dir / "academic_policies_2025.md"
    
    content = """---
title: "Admissions 2025"
category: "admissions"
authorization: "student"
scraped_date: 2025-06-15
---
# Main Section
This is some content for registration.
"""
    temp_file.write_text(content, encoding="utf-8")
    
    chunks = process_markdown_file(temp_file)
    
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["document_year"] == 2025
        assert chunk["start_line"] is not None
        assert chunk["end_line"] is not None


def test_club_roster_year_prefers_title_over_scraped_date(tmp_path):
    """Regression: Club Committee Data 24-25 must not become document_year=2026
    just because scraped_date is 2026-07-04 (the GDG convener hallucination)."""
    from metadata_extractors import (
        normalize_academic_year_label,
        resolve_document_academic_year,
    )

    assert normalize_academic_year_label("Club Committee Data 24-25") == "2024-25"
    assert normalize_academic_year_label("Club Committee C_DCs Information 2026-27") == "2026-27"
    assert normalize_academic_year_label("sbg_club_committee_c_dcs_information_2025_26.md") == "2025-26"
    assert normalize_academic_year_label("room 12-34") is None
    assert normalize_academic_year_label("hours 10-11") is None

    data_dir = tmp_path / "data" / "student_faculty"
    data_dir.mkdir(parents=True, exist_ok=True)
    old_roster = data_dir / "sbg_club_committee_data_24_25.md"
    old_roster.write_text(
        """---
title: "Club Committee Data 24-25"
scraped_date: "2026-07-04"
category: "SBG & Clubs - Clubs And Committees"
authorization: ["student", "faculty"]
---
# Club Committee Data 24-25
- GDG | Abhishek Abbi | Convener
""",
        encoding="utf-8",
    )
    new_roster = data_dir / "sbg_club_committee_c_dcs_information_2026_27.md"
    new_roster.write_text(
        """---
title: "Club Committee C_DCs Information 2026-27"
scraped_date: "2026-07-04"
category: "SBG & Clubs - Clubs And Committees"
authorization: ["student", "faculty"]
---
# Club Committee C_DCs Information 2026-27
- Google Developer Groups | Aditya Vaish | Convener
""",
        encoding="utf-8",
    )

    old_chunks = process_markdown_file(old_roster)
    new_chunks = process_markdown_file(new_roster)
    assert old_chunks[0]["document_year"] == 2024
    assert old_chunks[0]["academic_year"] == "2024-25"
    assert new_chunks[0]["document_year"] == 2026
    assert new_chunks[0]["academic_year"] == "2026-27"

    year, label = resolve_document_academic_year(
        {"title": "Club Committee Data 24-25", "scraped_date": "2026-07-04", "document_year": 2026},
        old_roster,
        "",
    )
    assert year == 2024
    assert label == "2024-25"


def test_context_builder_rule_year_from_short_title():
    from pipeline.retrieval.context_builder import ContextBuilder

    meta = {
        "title": "Club Committee Data 24-25",
        "document_year": 2026,  # wrong ingest artifact from scraped_date
        "scraped_date": "2026-07-04",
        "text": "GDG Convener Abhishek Abbi",
    }
    assert ContextBuilder._rule_year_from_metadata(meta) == "2024-25"


def test_academic_applicability_is_extracted_deterministically():
    metadata = {"title": "Academic Requirements BTech ICT 2021 wef Autumn 2021-22", "category": "Academics"}
    body = "These rules are applicable to students admitted to the program in the academic year 2021-22 and onwards."
    result = extract_academic_applicability(metadata, "data/academics/requirements.md", body)
    assert result == {
        "applicability_scope": "curriculum",
        "programme_id": "btech-ict",
        "degree_level": "undergraduate",
        "admission_year_from": 2021,
        "admission_year_to": 9999,
    }


def test_explicit_academic_applicability_takes_precedence():
    metadata = {
        "category": "Academics",
        "applicability_scope": "course",
        "programme_id": "btech-ict",
        "course_code": "ICT101",
        "degree_level": "undergraduate",
        "admission_year_from": "2024",
        "admission_year_to": "2026",
    }
    result = extract_academic_applicability(metadata, "data/academics/custom.md", "")
    assert result == {
        "applicability_scope": "course",
        "programme_id": "btech-ict",
        "course_code": "ICT101",
        "degree_level": "undergraduate",
        "admission_year_from": 2024,
        "admission_year_to": 2026,
    }
