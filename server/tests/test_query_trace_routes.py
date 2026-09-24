from __future__ import annotations
import datetime
import json
import os
import sys
from pathlib import Path
import uuid

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

SERVER_DIR = Path(__file__).resolve().parent.parent
RAG_DIR = SERVER_DIR / "rag"
sys.path.insert(0, str(SERVER_DIR))
sys.path.insert(0, str(RAG_DIR))

SECRET = "test-internal-secret-for-auth-middleware"
os.environ["INTERNAL_JWT_SECRET"] = SECRET

from api.auth import INTERNAL_JWT_AUDIENCE, INTERNAL_JWT_ISSUER
from api.routes import admin_routes

app = FastAPI()
app.include_router(admin_routes.router)
client = TestClient(app, raise_server_exceptions=False)


def make_token(erp_id: str = "ADMIN001", role: str = "admin") -> str:
    payload = {
        "erpId": erp_id,
        "role": role,
        "department": "ICT",
        "iss": INTERNAL_JWT_ISSUER,
        "aud": INTERNAL_JWT_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def auth_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or make_token()}"}


@pytest.fixture(autouse=True)
def mock_db(monkeypatch):
    test_id_1 = "11111111-1111-1111-1111-111111111111"
    test_id_2 = "22222222-2222-2222-2222-222222222222"

    sample_traces = [
        {
            "id": test_id_1,
            "created_at": datetime.datetime.utcnow(),
            "erp_id": "202101001",
            "user_role": "student",
            "user_dept": "ICT",
            "query_text": "What is the grading policy?",
            "query_type": "PUBLIC",
            "status": "passed",
            "failure_stage": "none",
            "failure_reason": None,
            "sources_fetched": [{"file": "grading_policy.pdf", "title": "Grading Policy"}],
            "sources_count": 1,
            "answer_preview": "The grading policy is relative.",
            "latency_total_ms": 1200,
            "latency_guardrail_ms": 50,
            "latency_retrieval_ms": 300,
            "latency_generation_ms": 850,
            "is_personal_data": False,
        },
        {
            "id": test_id_2,
            "created_at": datetime.datetime.utcnow() - datetime.timedelta(minutes=10),
            "erp_id": "202101002",
            "user_role": "student",
            "user_dept": "ICT",
            "query_text": "Show me someone else's grades",
            "query_type": "PERSONAL",
            "status": "failed",
            "failure_stage": "access_denied",
            "failure_reason": "ACCESS_CONTROL_DENIED",
            "sources_fetched": [],
            "sources_count": 0,
            "answer_preview": "I'm not able to retrieve that information.",
            "latency_total_ms": 150,
            "latency_guardrail_ms": 40,
            "latency_retrieval_ms": 0,
            "latency_generation_ms": 0,
            "is_personal_data": True,
        },
    ]

    def query(sql, params=()):
        sql_norm = " ".join(sql.split())

        # Check for role_bindings lookups used by _require_admin
        if "FROM role_bindings" in sql_norm:
            return [{"id": 1, "binding": "admin_staff", "revoked": False}]

        if "SELECT COUNT(*) AS total FROM query_trace_logs" in sql_norm:
            return [{"total": len(sample_traces)}]

        if "FROM query_trace_logs" in sql_norm and "ORDER BY created_at DESC" in sql_norm:
            return sample_traces

        if "FROM query_trace_logs" in sql_norm and "GROUP BY status" in sql_norm:
            return [
                {"status": "passed", "count": 1},
                {"status": "failed", "count": 1},
            ]

        if "FROM query_trace_logs" in sql_norm and "GROUP BY failure_stage" in sql_norm:
            return [
                {"failure_stage": "access_denied", "count": 1},
            ]

        if "FROM query_trace_logs" in sql_norm and "AVG(latency_total_ms)" in sql_norm:
            return [
                {
                    "avg_total": 675.0,
                    "avg_guardrail": 45.0,
                    "avg_retrieval": 150.0,
                    "avg_generation": 425.0,
                }
            ]

        if "FROM query_trace_logs WHERE id = %s" in sql_norm:
            target_id = params[0]
            for t in sample_traces:
                if t["id"] == str(target_id):
                    return [t]
            return []

        raise AssertionError(f"Unhandled query in mock: {sql_norm}")

    monkeypatch.setattr(admin_routes.db_conn, "query", query)


def test_list_query_traces_admin():
    res = client.get("/admin/queries", headers=auth_headers())
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["query_text"] == "What is the grading policy?"
    assert data["items"][0]["status"] == "passed"


def test_get_query_trace_stats():
    res = client.get("/admin/queries/stats", headers=auth_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["total_queries"] == 2
    assert data["passed_count"] == 1
    assert data["failed_count"] == 1
    assert data["pass_rate"] == 50.0
    assert data["top_failure_cause"] == "access_denied"
    assert len(data["failure_breakdown"]) == 1
    assert data["failure_breakdown"][0]["stage"] == "access_denied"


def test_get_query_trace_detail():
    res = client.get("/admin/queries/11111111-1111-1111-1111-111111111111", headers=auth_headers())
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "11111111-1111-1111-1111-111111111111"
    assert data["query_text"] == "What is the grading policy?"
    assert data["sources_count"] == 1


def test_get_query_trace_detail_not_found():
    res = client.get("/admin/queries/99999999-9999-9999-9999-999999999999", headers=auth_headers())
    assert res.status_code == 404
    assert res.json()["detail"] == "Query trace not found"


def test_student_forbidden():
    student_token = make_token(erp_id="202101001", role="student")
    res = client.get("/admin/queries", headers=auth_headers(student_token))
    assert res.status_code == 403
