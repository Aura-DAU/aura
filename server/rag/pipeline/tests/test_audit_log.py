"""
B8 acceptance tests — updated for SSO architecture.
AuditLog.record() no longer takes user_id (UUID). erp_id is the sole
requester identifier, matching the updated audit_log table schema.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
from unittest.mock import MagicMock
from audit_log import AuditLog


def make_audit(fail=False):
    mock_db = MagicMock()
    if fail:
        mock_db.execute.side_effect = Exception("Simulated DB failure")
    return AuditLog(db_module=mock_db), mock_db


def record_row(audit, *, granted, denial_reason=None):
    audit.record(
        erp_id="202301234",
        role="student",
        query_text="What is my CGPA?",
        query_type="personal",
        access_granted=granted,
        target_erp_id="202301234",
        denial_reason=denial_reason,
        erp_tables=["academic_record"],
    )


def test_five_records_produces_five_db_inserts():
    audit, mock_db = make_audit()
    for _ in range(3):
        record_row(audit, granted=True)
    for _ in range(2):
        record_row(audit, granted=False, denial_reason="denied")
    assert mock_db.execute.call_count == 5


def test_both_allowed_and_denied_rows_are_logged():
    audit, mock_db = make_audit()
    record_row(audit, granted=True)
    record_row(audit, granted=False, denial_reason="denied")
    assert mock_db.execute.call_count == 2
    calls = mock_db.execute.call_args_list
    # access_granted is 5th param (index 4) in new signature: erp_id, role, text, type, target, granted...
    # Let's just check both True and False appear somewhere in the args
    all_args = [c[0][1] for c in calls]
    granted_vals = [a[5] for a in all_args]  # access_granted is 6th element (index 5)
    assert True in granted_vals and False in granted_vals


def test_db_failure_does_not_raise_exception():
    audit, _ = make_audit(fail=True)
    record_row(audit, granted=True)   # must not raise


def test_db_failure_all_five_calls_still_complete():
    audit, _ = make_audit(fail=True)
    for _ in range(5):
        record_row(audit, granted=True)   # none must raise


def test_denial_reason_included_in_row():
    audit, mock_db = make_audit()
    record_row(audit, granted=False, denial_reason="no relationship found")
    args = mock_db.execute.call_args[0][1]
    assert "no relationship found" in args


def test_target_erp_id_included_in_row():
    audit, mock_db = make_audit()
    audit.record(
        erp_id="F1", role="faculty",
        query_text="Show S2 CGPA", query_type="personal",
        access_granted=True, target_erp_id="S2",
    )
    args = mock_db.execute.call_args[0][1]
    assert "S2" in args


def test_no_user_id_parameter_accepted():
    """Regression: record() must NOT accept a user_id kwarg (old interface)."""
    audit, _ = make_audit()
    with pytest.raises(TypeError):
        audit.record(
            user_id="some-uuid",   # should raise TypeError — param removed
            erp_id="202301234", role="student",
            query_text="q", query_type="personal", access_granted=True,
        )
