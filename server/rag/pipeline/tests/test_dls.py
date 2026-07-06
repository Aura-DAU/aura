import pytest
import os
import sys
from pathlib import Path

# Add rag directory to path so we can import from pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.retrieval.rbac import get_allowed_roles
from pipeline.retrieval.bm25_retriever import BM25Retriever

def test_rbac_additive_hierarchy():
    # Test base role
    assert get_allowed_roles("public") == ["public"]
    
    # Test inheritance
    student_roles = get_allowed_roles("student")
    assert "public" in student_roles
    assert "student" in student_roles
    
    # Test deep inheritance
    ug_convenor_roles = get_allowed_roles("faculty_convenor_ug")
    assert "public" in ug_convenor_roles
    assert "faculty" in ug_convenor_roles
    assert "faculty_coord" in ug_convenor_roles
    assert "faculty_convenor_ug" in ug_convenor_roles
    assert "faculty_convenor_pg" not in ug_convenor_roles
    
    # Test superadmin
    superadmin_roles = get_allowed_roles("superadmin")
    assert "public" in superadmin_roles
    assert "faculty" in superadmin_roles
    assert "student" in superadmin_roles
    assert "dean_academic" in superadmin_roles
    
    # Test admin
    admin_roles = get_allowed_roles("admin")
    assert "public" in admin_roles
    assert "faculty" in admin_roles
    assert "student" in admin_roles
    assert "dean_academic" in admin_roles
    
    # Test unknown role fallback
    assert get_allowed_roles("unknown_role") == ["public"]


def test_bm25_array_intersection_filter():
    # Dummy chunk data
    chunks = [
        {
            "chunk_id": "c1",
            "text": "Public document",
            "authorization": ["public"]
        },
        {
            "chunk_id": "c2",
            "text": "Internal committee",
            "authorization": ["faculty", "dean_academic"]
        },
        {
            "chunk_id": "c3",
            "text": "Senate minutes",
            "authorization": ["dean_academic", "superadmin"]
        }
    ]
    
    # Write dummy metadata to a temporary file
    import json
    import tempfile
    
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json") as f:
        json.dump(chunks, f)
        temp_path = f.name
        
    try:
        bm25 = BM25Retriever(temp_path)
        
        # Test student role (allowed: ["public", "student"])
        # Should only match chunk c1
        student_roles = get_allowed_roles("student")
        filter_student = {"authorization": {"$in": student_roles}}
        
        results_student = bm25.retrieve("document minutes", top_k=10, metadata_filter=filter_student, allowed_roles=student_roles)
        assert len(results_student) == 1
        assert results_student[0]["id"] == "c1"
        
        # Test faculty role (allowed: ["public", "faculty"])
        # Should match chunk c1, c2
        faculty_roles = get_allowed_roles("faculty")
        filter_faculty = {"authorization": {"$in": faculty_roles}}
        
        results_faculty = bm25.retrieve("document committee minutes", top_k=10, metadata_filter=filter_faculty, allowed_roles=faculty_roles)
        ids_faculty = {r["id"] for r in results_faculty}
        assert "c1" in ids_faculty
        assert "c2" in ids_faculty
        assert "c3" not in ids_faculty
        
        # Test superadmin (allowed: all roles)
        # Should match all 3
        superadmin_roles = get_allowed_roles("superadmin")
        filter_superadmin = {"authorization": {"$in": superadmin_roles}}
        
        results_sa = bm25.retrieve("document committee minutes", top_k=10, metadata_filter=filter_superadmin, allowed_roles=superadmin_roles)
        assert len(results_sa) == 3
        
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    pytest.main(["-v", __file__])
