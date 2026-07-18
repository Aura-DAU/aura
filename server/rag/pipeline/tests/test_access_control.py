import pytest
from pipeline.personal_data.access_control import authorize_personal_query, AccessDenied


def test_student_can_access_own_data_with_no_target():
    result = authorize_personal_query({"role": "student", "erp_id": "S1"}, None)
    assert result == "S1"


def test_student_can_access_own_data_with_explicit_self_target():
    result = authorize_personal_query({"role": "student", "erp_id": "S1"}, "S1")
    assert result == "S1"


def test_student_cannot_access_another_students_data():
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "student", "erp_id": "S1"}, "S2")


def test_faculty_must_specify_a_target():
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "faculty", "erp_id": "F1"}, None)


def test_faculty_with_valid_target_is_authorized():
    result = authorize_personal_query({"role": "faculty", "erp_id": "F1"}, "S1")
    assert result == "S1"


def test_faculty_cannot_target_their_own_erp_id_as_a_student_record():
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "faculty", "erp_id": "F1"}, "F1")


def test_unrecognized_role_is_denied():
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "guest", "erp_id": "X1"}, "S1")


def test_missing_identity_fields_denied_not_default_allowed():
    with pytest.raises(AccessDenied):
        authorize_personal_query({"erp_id": "S1"}, None)  # no role
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "student"}, None)  # no erp_id
    with pytest.raises(AccessDenied):
        authorize_personal_query(None, "S2")  # no identity at all


def test_role_cannot_be_spoofed_via_arbitrary_string():
    # Regression guard for the original vulnerability this whole layer
    # exists to fix: a client claiming role='professor' (the old, unverified
    # field name) must not slip through as faculty.
    with pytest.raises(AccessDenied):
        authorize_personal_query({"role": "professor", "erp_id": "F1"}, "S1")
