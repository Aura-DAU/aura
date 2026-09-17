import datetime
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

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
from pipeline.tracer import (
    is_tracing_enabled,
    create_trace_config,
    get_langsmith_run_url,
    get_langfuse_trace_url,
    get_trace_url,
    get_active_provider,
    wrap_openai_client,
)
from pipeline.failure_logger import record_query_failure
from pipeline.chat_history_logger import record_chat_turn

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
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def auth_headers(token: str | None = None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token or make_token()}"}


# ── 1. Unified Tracer & Provider Tests ────────────────────────────────────────

def test_tracer_disabled_by_default(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert get_active_provider() == "none"
    assert not is_tracing_enabled()


def test_tracer_langfuse_enabled(monkeypatch):
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test-1234")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test-5678")
    assert get_active_provider() == "langfuse"
    assert is_tracing_enabled()


def test_tracer_langsmith_fallback_enabled(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.setenv("LANGCHAIN_API_KEY", "ls__test_key_12345")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    assert get_active_provider() == "langsmith"
    assert is_tracing_enabled()


def test_create_trace_config():
    config, collector = create_trace_config(
        run_name="aura_query_test",
        thread_id="thread_xyz",
        erp_id="202101001",
        role="student",
        metadata={"custom_flag": True},
    )
    assert collector is not None
    assert "metadata" in config
    assert config["metadata"]["thread_id"] == "thread_xyz"
    assert config["metadata"]["erp_id"] == "202101001"
    assert config["metadata"]["role"] == "student"
    assert config["metadata"]["custom_flag"] is True
    assert "student" in config["tags"]


def test_get_langfuse_trace_url(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.delenv("LANGFUSE_PROJECT_ID", raising=False)
    url = get_langfuse_trace_url("tr_abc123")
    assert url == "https://cloud.langfuse.com/trace/tr_abc123"

    monkeypatch.setenv("LANGFUSE_PROJECT_ID", "p_dau42")
    url_with_proj = get_langfuse_trace_url("tr_abc123")
    assert url_with_proj == "https://cloud.langfuse.com/project/p_dau42/traces/tr_abc123"

    assert get_langfuse_trace_url(None) is None


def test_get_langsmith_run_url(monkeypatch):
    monkeypatch.setenv("LANGCHAIN_PROJECT", "test-aura-project")
    url = get_langsmith_run_url("run_123456")
    assert "smith.langchain.com" in url
    assert "run_123456" in url
    assert "test-aura-project" in url

    # None if run_id is None
    assert get_langsmith_run_url(None) is None


def test_get_trace_url_dynamic(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert get_trace_url("trace_999") is None

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-1")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-1")
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    assert get_trace_url("trace_999") == "https://cloud.langfuse.com/trace/trace_999"


def test_wrap_openai_client_graceful():
    mock_client = MagicMock()
    wrapped = wrap_openai_client(mock_client)
    assert wrapped is not None


# ── 2. Failure Logger & Chat History Logger Graceful Degradation ───────────────

def test_record_query_failure_graceful_without_db(monkeypatch):
    # Should catch DB error and not raise
    monkeypatch.setattr("db.connection.execute", MagicMock(side_effect=RuntimeError("DB down")))
    record_query_failure(
        stage="guardrail",
        error_code="GUARDRAIL_BLOCKED",
        error_message="Test guardrail violation",
        query="drop table users",
        thread_id="thread_test",
        erp_id="202101001",
        role="student",
    )


def test_record_chat_turn_graceful_without_db(monkeypatch):
    # Should catch DB error and not raise
    monkeypatch.setattr("db.connection.execute", MagicMock(side_effect=RuntimeError("DB down")))
    record_chat_turn(
        thread_id="thread_test",
        erp_id="202101001",
        role="student",
        user_message="When is exams?",
        assistant_message="Exams start May 1st.",
    )


# ── 3. Admin Endpoints Authentication & Logic ──────────────────────────────────

def test_admin_failures_endpoints_require_admin():
    student_headers = auth_headers(make_token(erp_id="202101001", role="student"))

    res = client.get("/admin/failures/summary", headers=student_headers)
    assert res.status_code == 403

    res = client.get("/admin/failures", headers=student_headers)
    assert res.status_code == 403

    res = client.get("/admin/conversations", headers=student_headers)
    assert res.status_code == 403


def test_admin_failures_summary(monkeypatch):
    admin_headers = auth_headers(make_token(erp_id="ADMIN001", role="admin"))

    def mock_query(sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM role_bindings" in sql_norm:
            return [{"binding": "admin_staff"}]
        if "FROM query_failures" in sql_norm and "GROUP BY stage" in sql_norm:
            return [{"stage": "guardrail", "count": 5}, {"stage": "retrieval", "count": 2}]
        if "FROM query_failures" in sql_norm and "GROUP BY error_code" in sql_norm:
            return [{"error_code": "GUARDRAIL_BLOCKED", "count": 5}]
        if "FROM query_failures" in sql_norm and "GROUP BY TO_CHAR" in sql_norm:
            return [{"date": "2026-09-11", "count": 7}]
        if "SELECT count(*) as count FROM query_failures" in sql_norm:
            return [{"count": 7}]
        if "SELECT count(*) as count FROM latency_logs" in sql_norm:
            return [{"count": 70}]
        return []

    monkeypatch.setattr("db.connection.query", mock_query)

    res = client.get("/admin/failures/summary?days=7", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_failures"] == 7
    assert data["total_queries"] == 70
    assert data["failure_rate"] == 10.0
    assert len(data["by_stage"]) == 2
    assert len(data["by_code"]) == 1


def test_admin_failures_list_and_resolve(monkeypatch):
    admin_headers = auth_headers(make_token(erp_id="ADMIN001", role="admin"))

    sample_item = {
        "id": 1,
        "stage": "guardrail",
        "error_code": "GUARDRAIL_BLOCKED",
        "error_message": "Prompt injection detected",
        "query": "ignore instructions",
        "thread_id": "thread_abc",
        "erp_id": "202101001",
        "role": "student",
        "langsmith_run_id": "run_999",
        "langsmith_url": None,
        "created_at": "2026-09-11T09:00:00Z",
        "resolved_at": None,
        "resolved_by": None,
    }

    def mock_query(sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM role_bindings" in sql_norm:
            return [{"binding": "admin_staff"}]
        if "SELECT count(*) as count FROM query_failures" in sql_norm:
            return [{"count": 1}]
        if "SELECT id, stage, error_code" in sql_norm:
            return [sample_item]
        return []

    monkeypatch.setattr("db.connection.query", mock_query)
    monkeypatch.setattr("db.connection.execute", MagicMock(return_value=1))

    res = client.get("/admin/failures?days=7&stage=guardrail", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    # Check that langsmith_url and trace_id/trace_url were populated from run_id
    assert data["items"][0]["langsmith_url"] is not None
    assert data["items"][0]["trace_id"] == "run_999"
    assert "trace_url" in data["items"][0]

    resolve_res = client.post("/admin/failures/1/resolve", headers=admin_headers)
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "ok"


def test_admin_conversations_list_and_detail(monkeypatch):
    admin_headers = auth_headers(make_token(erp_id="ADMIN001", role="admin"))

    sample_thread = {
        "thread_id": "t_1001",
        "erp_id": "202101001",
        "role": "student",
        "title": "Semester Exam Schedule",
        "turn_count": 2,
        "created_at": "2026-09-11T08:00:00Z",
        "last_active_at": "2026-09-11T08:05:00Z",
    }
    sample_messages = [
        {
            "id": 1,
            "thread_id": "t_1001",
            "role": "user",
            "content": "When are midterms?",
            "sources": [],
            "is_personal_data": False,
            "langsmith_run_id": None,
            "created_at": "2026-09-11T08:00:00Z",
        },
        {
            "id": 2,
            "thread_id": "t_1001",
            "role": "assistant",
            "content": "Midterms start Oct 10th.",
            "sources": [{"file": "academic_calendar.pdf"}],
            "is_personal_data": False,
            "langsmith_run_id": "run_msg_1",
            "created_at": "2026-09-11T08:00:02Z",
        }
    ]

    def mock_query(sql, params=()):
        sql_norm = " ".join(sql.split())
        if "FROM role_bindings" in sql_norm:
            return [{"binding": "admin_staff"}]
        if "SELECT count(*) as count FROM chat_threads" in sql_norm:
            return [{"count": 1}]
        if "SELECT thread_id, erp_id, role, title" in sql_norm and "WHERE thread_id = %s" not in sql_norm:
            return [sample_thread]
        if "FROM chat_threads WHERE thread_id = %s" in sql_norm:
            return [sample_thread]
        if "FROM chat_messages WHERE thread_id = %s" in sql_norm:
            return sample_messages
        return []

    monkeypatch.setattr("db.connection.query", mock_query)

    list_res = client.get("/admin/conversations", headers=admin_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] == 1

    detail_res = client.get("/admin/conversations/t_1001", headers=admin_headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["thread"]["thread_id"] == "t_1001"
    assert len(detail["messages"]) == 2
    assert detail["messages"][1]["langsmith_url"] is not None
    assert detail["messages"][1]["trace_id"] == "run_msg_1"
    assert "trace_url" in detail["messages"][1]
