import sys
from pathlib import Path

# Add chunking directory to path so local imports resolve correctly
chunking_dir = Path(__file__).resolve().parent.parent / "ingestion" / "chunking"
sys.path.insert(0, str(chunking_dir))

import pytest
from section_extracter import extract_sections
from process_corpus import find_line_range_in_file, process_markdown_file

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
