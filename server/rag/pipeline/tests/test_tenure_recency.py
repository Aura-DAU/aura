import sys
from pathlib import Path

# Add chunking directory to path so process_corpus can be imported
chunking_dir = Path(__file__).resolve().parent.parent / "ingestion" / "chunking"
sys.path.insert(0, str(chunking_dir))

from process_corpus import extract_academic_or_calendar_year
from pipeline.retrieval.context_builder import ContextBuilder
from pipeline.retrieval.reranker import Reranker


def test_extract_academic_or_calendar_year():
    # 4-digit academic ranges
    assert extract_academic_or_calendar_year("Academic Requirements PhD wef 2024-25") == "2024-25"
    assert extract_academic_or_calendar_year("SBG Club Committee C DCS Information 2025_26") == "2025-26"
    assert extract_academic_or_calendar_year("Tenure 2026 27 Core Members") == "2026-27"
    
    # 2-digit academic ranges
    assert extract_academic_or_calendar_year("Club Committee Data 24-25") == "2024-25"
    assert extract_academic_or_calendar_year("sbg_tenure_25_26_core_members_name.md") == "2025-26"
    assert extract_academic_or_calendar_year("sbg_club_committee_c_dcs_information_2026_27.md") == "2026-27"
    
    # 4-digit calendar year
    assert extract_academic_or_calendar_year("academic_policies_2025.md") == 2025
    assert extract_academic_or_calendar_year("2025-06-15") == 2025


def test_context_builder_rule_year_formatting():
    builder = ContextBuilder()
    chunks = [
        {
            "metadata": {
                "title": "Tenure 25-26 Core Members Name",
                "document_year": "2025-26",
                "text": "Academic Committee Convener: Jas Mehta",
                "start_line": 1,
                "end_line": 10
            }
        },
        {
            "metadata": {
                "title": "Club Committee Data 24-25",
                "text": "Academic Committee Convener: Yash Tarpara",
                "start_line": 1,
                "end_line": 10
            }
        }
    ]
    
    res = builder.build(chunks)
    context = res["context"]
    assert 'rule_year="2025-26"' in context
    assert 'rule_year="2024-25"' in context


def test_reranker_extract_start_year():
    reranker = Reranker.__new__(Reranker)
    
    meta1 = {"title": "Tenure 25-26 Core Members Name"}
    meta2 = {"title": "Club Committee Data 24-25"}
    meta3 = {"document_year": 2026}
    meta4 = {"rule_year": "2024-25"}
    
    assert reranker._extract_start_year(meta1) == 2025
    assert reranker._extract_start_year(meta2) == 2024
    assert reranker._extract_start_year(meta3) == 2026
    assert reranker._extract_start_year(meta4) == 2024
