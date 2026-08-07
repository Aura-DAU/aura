import datetime
import json
import sys
from pathlib import Path

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

SERVER_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = SERVER_DIR / "rag"
sys.path.insert(0, str(SERVER_DIR))
sys.path.insert(0, str(RAG_DIR))

SECRET = "test-internal-secret-for-auth-middleware"
import os

os.environ["INTERNAL_JWT_SECRET"] = SECRET

from api.auth import INTERNAL_JWT_AUDIENCE, INTERNAL_JWT_ISSUER
from api.routes import admin_routes

app = FastAPI()
app.include_router(admin_routes.router)
client = TestClient(app, raise_server_exceptions=False)


def make_admin_token(erp_id: str = "ADMIN001") -> str:
    payload = {
        "erpId": erp_id,
        "role": "admin",
        "department": "ICT",
        "iss": INTERNAL_JWT_ISSUER,
        "aud": INTERNAL_JWT_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def auth_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or make_admin_token()}"}


@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    store = {
        "users": {},
        "bindings": [],
    }

    def query(sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM user_identity_map uim" in sql_norm and "role = 'admin'" in sql_norm:
            admins = [
                u for u in store["users"].values()
                if u["role"] == "admin" and u["is_active"]
            ]
            return [
                {
                    "email": u["email"],
                    "erp_id": u["erp_id"],
                    "dept": u.get("dept"),
                    "created_at": u.get("created_at"),
                    "has_admin_staff_binding": any(
                        b["erp_id"] == u["erp_id"]
                        and b["binding"] == "admin_staff"
                        and not b["revoked"]
                        for b in store["bindings"]
                    ),
                }
                for u in admins
            ]

        if "FROM user_identity_map WHERE email = %s OR erp_id = %s" in sql_norm:
            email, erp_id = params
            for u in store["users"].values():
                if u["email"] == email or u["erp_id"] == erp_id:
                    return [{"erp_id": u["erp_id"], "email": u["email"]}]
            return []

        if "FROM user_identity_map WHERE email = %s" in sql_norm and "OR erp_id" not in sql_norm:
            email = params[0]
            u = store["users"].get(email)
            return [u] if u else []

        if "FROM role_bindings" in sql_norm and "SELECT id FROM" in sql_norm:
            erp_id = params[0]
            binding = params[1] if len(params) > 1 else "admin_staff"
            return [
                b for b in store["bindings"]
                if b["erp_id"] == erp_id and b["binding"] == binding and not b["revoked"]
            ]

        raise AssertionError(f"Unexpected query: {sql_norm} params={params}")

    def execute(sql, params=()):
        sql_norm = " ".join(sql.split())
        if sql_norm.startswith("INSERT INTO user_identity_map"):
            email, erp_id, role, dept, *_rest = params[:4]
            store["users"][email] = {
                "email": email,
                "erp_id": erp_id,
                "role": role,
                "dept": dept,
                "is_active": True,
                "created_at": "2026-01-01T00:00:00Z",
            }
            return

        if sql_norm.startswith("INSERT INTO role_bindings"):
            erp_id, binding, granted_by = params[:3]
            expires_at = params[3] if len(params) > 3 else None
            store["bindings"].append(
                {
                    "id": f"binding-{len(store['bindings']) + 1}",
                    "erp_id": erp_id,
                    "binding": binding,
                    "granted_by": granted_by,
                    "expires_at": expires_at,
                    "revoked": False,
                }
            )
            return

        if "UPDATE user_identity_map SET is_active = FALSE" in sql_norm:
            email = params[0]
            if email in store["users"]:
                store["users"][email]["is_active"] = False
            return

        if "UPDATE user_identity_map" in sql_norm and "SET role =" in sql_norm:
            role, email = params
            if email in store["users"]:
                store["users"][email]["role"] = role
                store["users"][email]["is_active"] = True
            return

        if "UPDATE role_bindings SET revoked = TRUE" in sql_norm:
            erp_id, binding = params
            for b in store["bindings"]:
                if b["erp_id"] == erp_id and b["binding"] == binding and not b["revoked"]:
                    b["revoked"] = True
            return

        raise AssertionError(f"Unexpected execute: {sql_norm} params={params}")

    monkeypatch.setattr(admin_routes.db_conn, "query", query)
    monkeypatch.setattr(admin_routes.db_conn, "execute", execute)
    monkeypatch.setattr(
        admin_routes,
        "resolve_effective_role",
        lambda identity: "admin_staff" if identity.role == "admin" else identity.role,
    )
    return store


def test_grant_dashboard_access_infers_student_erp_id(mock_db):
    res = client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "202401401@dau.ac.in"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "granted"
    assert data["erp_id"] == "202401401"
    assert data["admin_staff_binding_added"] is True
    assert mock_db["users"]["202401401@dau.ac.in"]["role"] == "admin"


def test_grant_dashboard_access_requires_erp_id_for_faculty_email(mock_db):
    res = client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "prof.sharma@dau.ac.in"},
    )
    assert res.status_code == 400
    assert "erp_id is required" in res.json()["detail"]


def test_grant_dashboard_access_with_explicit_erp_id(mock_db):
    res = client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "prof.sharma@dau.ac.in", "erp_id": "FAC001"},
    )
    assert res.status_code == 200
    assert res.json()["erp_id"] == "FAC001"


def test_grant_rejects_non_dau_domain(mock_db):
    res = client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "user@gmail.com"},
    )
    assert res.status_code == 400


def test_list_dashboard_access(mock_db):
    client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "202401475@dau.ac.in"},
    )
    res = client.get("/admin/users/access", headers=auth_headers())
    assert res.status_code == 200
    admins = res.json()["admins"]
    assert len(admins) == 1
    assert admins[0]["email"] == "202401475@dau.ac.in"


def test_revoke_dashboard_access(mock_db):
    client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "202401475@dau.ac.in"},
    )
    res = client.request(
        "DELETE",
        "/admin/users/access",
        headers={
            **auth_headers(make_admin_token("ADMIN001")),
            "Content-Type": "application/json",
        },
        content=json.dumps({"email": "202401475@dau.ac.in"}),
    )
    assert res.status_code == 200
    assert res.json()["status"] == "revoked"
    assert res.json()["restored_role"] == "student"
    user = mock_db["users"]["202401475@dau.ac.in"]
    # Revoke must demote, not deactivate — is_active=FALSE bans SSO login.
    assert user["is_active"] is True
    assert user["role"] == "student"
    assert all(
        b["revoked"]
        for b in mock_db["bindings"]
        if b["erp_id"] == "202401475" and b["binding"] == "admin_staff"
    )


def test_revoke_faculty_admin_restores_faculty_role(mock_db):
    client.post(
        "/admin/users/access",
        headers=auth_headers(),
        json={"email": "prof.sharma@dau.ac.in", "erp_id": "FAC001"},
    )
    res = client.request(
        "DELETE",
        "/admin/users/access",
        headers={
            **auth_headers(make_admin_token("ADMIN001")),
            "Content-Type": "application/json",
        },
        content=json.dumps({"email": "prof.sharma@dau.ac.in"}),
    )
    assert res.status_code == 200
    assert res.json()["restored_role"] == "faculty"
    user = mock_db["users"]["prof.sharma@dau.ac.in"]
    assert user["is_active"] is True
    assert user["role"] == "faculty"


def test_revoke_blocks_self(mock_db):
    client.post(
        "/admin/users/access",
        headers=auth_headers(make_admin_token("ADMIN001")),
        json={"email": "admin@dau.ac.in", "erp_id": "ADMIN001"},
    )
    res = client.request(
        "DELETE",
        "/admin/users/access",
        headers={
            **auth_headers(make_admin_token("ADMIN001")),
            "Content-Type": "application/json",
        },
        content=json.dumps({"email": "admin@dau.ac.in"}),
    )
    assert res.status_code == 400
    assert "your own" in res.json()["detail"].lower()
