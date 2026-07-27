# Tests for GET /internal/resolve-identity.
# Verifies: secret header enforcement, domain validation, found/not-found
# behaviour. Does not need a real DB — uses a mock db_conn module.

import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

os.environ["INTERNAL_RESOLVE_SECRET"] = "test-resolve-secret"

# Build a minimal FastAPI app with just the identity router
from api.routes.identity_routes import router
app = FastAPI()
app.include_router(router)
client = TestClient(app)

GOOD_HEADERS = {"X-Internal-Secret": "test-resolve-secret"}
BAD_HEADERS  = {"X-Internal-Secret": "wrong-secret"}


def _mock_db(rows):
    mock = MagicMock()
    mock.query.return_value = rows
    return mock


def test_missing_secret_returns_422():
    # No header at all → FastAPI returns 422 (missing required header)
    res = client.get("/internal/resolve-identity?email=test@dau.ac.in")
    assert res.status_code == 422


def test_wrong_secret_returns_403():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])):
        res = client.get("/internal/resolve-identity?email=test@dau.ac.in",
                         headers=BAD_HEADERS)
    assert res.status_code == 403


def test_disallowed_domain_returns_400():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])):
        res = client.get("/internal/resolve-identity?email=test@gmail.com",
                         headers=GOOD_HEADERS)
    assert res.status_code == 400
    assert "domain" in res.json()["detail"].lower()


def test_unknown_email_returns_guest():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])):
        res = client.get("/internal/resolve-identity?email=unknown@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "guest"
    assert data["erp_id"] == "GUEST_UNKNOWN"


def test_valid_range_student_email_resolves():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])) as mock_db:
        res = client.get("/internal/resolve-identity?email=202401475@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "student"
    assert data["erp_id"] == "202401475"
    assert data["department"] == "ICTCS"  # prog code "014" → ICTCS
    # Ensure write-through cache called db_conn.execute
    assert mock_db.execute.called


# ---------------------------------------------------------------------------
# Branch-code parsing tests (dynamic fallback path, no DB row)
# ERP ID format: YYYY PP XXXXX  (PP = 2-digit program code at index 4:6)
# ---------------------------------------------------------------------------

def _student_dept(erp_id: str) -> str:
    """Helper: fetch dept for a fresh student login (no DB row)."""
    with patch("api.routes.identity_routes.db_conn", _mock_db([])):
        res = client.get(f"/internal/resolve-identity?email={erp_id}@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    return res.json()["department"]


def test_branch_code_ict():
    # prog code "01" (e.g. 202401001) → ICT
    assert _student_dept("202401001") == "ICT"


def test_branch_code_ict_cs():
    # prog code "014" (e.g. 202401401) → ICTCS
    assert _student_dept("202401401") == "ICTCS"


def test_branch_code_mnc():
    # prog code "03" (e.g. 202403001) → MnC
    assert _student_dept("202403001") == "MnC"


def test_branch_code_evd():
    # prog code "04" (e.g. 202404001) → EVD
    assert _student_dept("202404001") == "EVD"


def test_branch_code_mtech():
    # prog code "11" (e.g. 202411001) → MTech
    assert _student_dept("202411001") == "MTech"


def test_branch_code_mscit():
    # prog code "12" (e.g. 202412001) → MScIT
    assert _student_dept("202412001") == "MScIT"


def test_branch_code_mscds():
    # prog code "18" (e.g. 202418001) → MScDS
    assert _student_dept("202418001") == "MScDS"


def test_branch_code_phd():
    # prog code "21" (e.g. 202421001) → PhD
    assert _student_dept("202421001") == "PhD"


def test_branch_code_unknown_defaults_to_ict():
    # prog code "99" (unknown) → safe default ICT
    assert _student_dept("202499001") == "ICT"




def test_out_of_range_student_email_resolves_as_guest():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])) as mock_db:
        res = client.get("/internal/resolve-identity?email=202101002@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "guest"
    assert data["erp_id"] == "GUEST_202101002"
    # Guests should not be cached in DB
    assert not mock_db.execute.called


def test_matching_faculty_email_resolves():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])) as mock_db:
        res = client.get("/internal/resolve-identity?email=abhishek.gupta@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "faculty"
    assert data["erp_id"] == "FAC_ABHISHEK.GUPTA"
    assert mock_db.execute.called


def test_non_matching_faculty_email_resolves_as_guest():
    with patch("api.routes.identity_routes.db_conn", _mock_db([])) as mock_db:
        res = client.get("/internal/resolve-identity?email=notafaculty@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "guest"
    assert data["erp_id"] == "GUEST_NOTAFACULTY"
    assert not mock_db.execute.called


def test_known_student_email_returns_identity():
    fake_row = [{"erp_id": "202301234", "role": "student", "dept": "ICT"}]
    with patch("api.routes.identity_routes.db_conn", _mock_db(fake_row)):
        res = client.get("/internal/resolve-identity?email=parth@dau.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert data["erp_id"]     == "202301234"
    assert data["role"]        == "student"
    assert data["department"]  == "ICT"


def test_known_faculty_email_returns_faculty_role():
    fake_row = [{"erp_id": "FAC001", "role": "faculty", "dept": "ICT"}]
    with patch("api.routes.identity_routes.db_conn", _mock_db(fake_row)):
        res = client.get("/internal/resolve-identity?email=prof@daiict.ac.in",
                         headers=GOOD_HEADERS)
    assert res.status_code == 200
    assert res.json()["role"] == "faculty"


def test_both_dau_and_daiict_domains_accepted():
    fake_row = [{"erp_id": "S1", "role": "student", "dept": "ICT"}]
    for domain in ("dau.ac.in", "daiict.ac.in"):
        with patch("api.routes.identity_routes.db_conn", _mock_db(fake_row)):
            res = client.get(f"/internal/resolve-identity?email=user@{domain}",
                             headers=GOOD_HEADERS)
        assert res.status_code == 200, f"domain {domain} should be accepted"
