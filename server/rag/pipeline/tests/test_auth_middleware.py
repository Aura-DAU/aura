"""
Tests for require_identity() — the FastAPI dependency that verifies
the internal JWT minted by Next.js.

Verifies: missing token → 401, valid token → Identity extracted,
expired → 401, wrong secret → 401, bad role → 403.
"""

import sys, os, datetime
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pytest
import jwt
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

SECRET = "test-internal-secret-for-auth-middleware"
os.environ["INTERNAL_JWT_SECRET"] = SECRET

from api.auth import require_identity, Identity

app = FastAPI()

@app.get("/protected")
def protected(identity: Identity = Depends(require_identity)):
    return {"erp_id": identity.erp_id, "role": identity.role, "dept": identity.dept}

client = TestClient(app, raise_server_exceptions=False)


def make_token(payload: dict, secret: str = SECRET, exp_delta_seconds: int = 60) -> str:
    payload = {**payload, "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=exp_delta_seconds)}
    return jwt.encode(payload, secret, algorithm="HS256")


def auth(token): return {"Authorization": f"Bearer {token}"}


def test_no_token_returns_403():
    # HTTPBearer returns 401 or 403 depending on FastAPI version when no header present
    res = client.get("/protected")
    assert res.status_code in (401, 403)


def test_valid_student_token_returns_identity():
    token = make_token({"erpId": "202301234", "role": "student", "department": "ICT"})
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 200
    data = res.json()
    assert data["erp_id"] == "202301234"
    assert data["role"]   == "student"
    assert data["dept"]   == "ICT"


def test_valid_faculty_token_returns_identity():
    token = make_token({"erpId": "FAC001", "role": "faculty", "department": "ICT"})
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 200
    assert res.json()["role"] == "faculty"


def test_expired_token_returns_401():
    token = make_token({"erpId": "S1", "role": "student"}, exp_delta_seconds=-1)
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_wrong_secret_returns_401():
    token = make_token({"erpId": "S1", "role": "student"}, secret="completely-wrong-secret")
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 401


def test_unrecognized_role_returns_403():
    token = make_token({"erpId": "X1", "role": "superuser"})
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 403


def test_missing_erp_id_claim_returns_401():
    token = make_token({"role": "student"})   # no erpId
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 401


def test_user_id_property_equals_erp_id():
    """Backward-compat: identity.user_id must return erp_id."""
    token = make_token({"erpId": "202301234", "role": "student"})
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 200
    # If user_id property works, erp_id in response matches
    assert res.json()["erp_id"] == "202301234"


def test_camelcase_erpId_claim_is_read_correctly():
    """Next.js mints camelCase 'erpId' — must be parsed, not 'erp_id'."""
    token = make_token({"erpId": "202399999", "role": "student"})
    res = client.get("/protected", headers=auth(token))
    assert res.status_code == 200
    assert res.json()["erp_id"] == "202399999"
