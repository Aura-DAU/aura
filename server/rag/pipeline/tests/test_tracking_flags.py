import pytest
import os
import json
from unittest.mock import patch, mock_open
from pipeline.personal_data.tracking_store import get_tracking_flags, update_tracking_flags
from api.request_context import RequestContext, AcademicScopeResolver
from api.auth import Identity

@pytest.fixture
def mock_tracking_file(tmp_path):
    file_path = tmp_path / "tracking_flags.json"
    with patch("pipeline.personal_data.tracking_store._STORE_PATH", str(file_path)):
        yield str(file_path)

def test_get_and_update_tracking_flags(mock_tracking_file):
    # Should return empty dict initially
    assert get_tracking_flags("student1") == {}

    # Update with some flags
    updated = update_tracking_flags("student1", {"dob": "1999-01-01", "likes": "pizza"})
    assert updated == {"dob": "1999-01-01", "likes": "pizza"}

    # Update with more flags, should merge
    updated = update_tracking_flags("student1", {"likes": "pasta", "city": "NYC"})
    assert updated == {"dob": "1999-01-01", "likes": "pasta", "city": "NYC"}

    # Another user should not interfere
    update_tracking_flags("student2", {"city": "London"})
    assert get_tracking_flags("student1") == {"dob": "1999-01-01", "likes": "pasta", "city": "NYC"}
    assert get_tracking_flags("student2") == {"city": "London"}

@patch("pipeline.personal_data.tracking_store.get_tracking_flags")
def test_academic_scope_resolver_includes_tracking_flags(mock_get_tracking_flags):
    mock_get_tracking_flags.return_value = {"dob": "2000-01-01"}
    
    resolver = AcademicScopeResolver()
    
    # Test for non-student
    identity_faculty = Identity(erp_id="fac1", role="faculty")
    context_faculty = resolver.resolve(identity_faculty, "faculty")
    assert context_faculty.tracking_flags == {"dob": "2000-01-01"}
    
    # Test for student (mocking DB is complex, but we can see if it sets flags even if DB fails)
    identity_student = Identity(erp_id="stu1", role="student")
    with patch("db.connection.query") as mock_query:
        mock_query.return_value = [] # simulates no DB rows, falls back
        context_student = resolver.resolve(identity_student, "student")
        assert context_student.tracking_flags == {"dob": "2000-01-01"}
