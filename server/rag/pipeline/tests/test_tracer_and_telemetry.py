import os
from unittest.mock import MagicMock
import pytest

from pipeline.tracer import (
    is_tracing_enabled,
    create_trace_config,
    get_langsmith_run_url,
    get_langfuse_trace_url,
    get_trace_url,
    get_active_provider,
    wrap_openai_client,
    RootRunCollector,
)
from pipeline.failure_logger import record_query_failure
from pipeline.chat_history_logger import record_chat_turn


def test_tracer_provider_detection(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert get_active_provider() == "none"
    assert not is_tracing_enabled()

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-live")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-live")
    assert get_active_provider() == "langfuse"
    assert is_tracing_enabled()

    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.setenv("LANGSMITH_API_KEY", "ls-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    assert get_active_provider() == "langsmith"
    assert is_tracing_enabled()


def test_langfuse_url_generation(monkeypatch):
    monkeypatch.setenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    monkeypatch.delenv("LANGFUSE_PROJECT_ID", raising=False)
    url = get_langfuse_trace_url("tr_123")
    assert url == "https://cloud.langfuse.com/trace/tr_123"

    monkeypatch.setenv("LANGFUSE_PROJECT_ID", "proj_aura")
    url_p = get_langfuse_trace_url("tr_123")
    assert url_p == "https://cloud.langfuse.com/project/proj_aura/traces/tr_123"

    assert get_langfuse_trace_url(None) is None


def test_langsmith_url_generation(monkeypatch):
    monkeypatch.setenv("LANGSMITH_PROJECT", "custom-smith-project")
    url = get_langsmith_run_url("run_456")
    assert "smith.langchain.com" in url
    assert "run_456" in url
    assert "custom-smith-project" in url

    assert get_langsmith_run_url(None) is None


def test_dynamic_get_trace_url(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    monkeypatch.delenv("LANGCHAIN_API_KEY", raising=False)
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)
    assert get_trace_url("tr_789") is None

    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    monkeypatch.setenv("LANGFUSE_HOST", "http://localhost:3000")
    assert get_trace_url("tr_789") == "http://localhost:3000/trace/tr_789"


def test_create_trace_config_tags_and_metadata():
    config, collector = create_trace_config(
        run_name="aura_unit_test",
        thread_id="th_123",
        erp_id="202101099",
        role="faculty",
        metadata={"unit": "test"},
        tags=["experimental"],
    )
    assert isinstance(collector, RootRunCollector)
    assert collector.run_id is not None
    assert config["metadata"]["thread_id"] == "th_123"
    assert config["metadata"]["erp_id"] == "202101099"
    assert config["metadata"]["role"] == "faculty"
    assert config["metadata"]["unit"] == "test"
    assert "faculty" in config["tags"]
    assert "experimental" in config["tags"]


def test_wrap_openai_client_noop():
    mock_client = MagicMock()
    wrapped = wrap_openai_client(mock_client)
    assert wrapped is not None


def test_failure_logger_safe_without_db(monkeypatch):
    monkeypatch.setattr("db.connection.execute", MagicMock(side_effect=RuntimeError("Auth DB offline")))
    record_query_failure(
        stage="tool_execution",
        error_code="TOOL_TIMEOUT",
        error_message="Tool call took too long",
        query="show timetable",
        thread_id="th_001",
        erp_id="202101001",
        role="student",
        trace_id="tr_timeout_1",
        trace_url="https://cloud.langfuse.com/trace/tr_timeout_1",
    )


def test_chat_history_logger_safe_without_db(monkeypatch):
    monkeypatch.setattr("db.connection.execute", MagicMock(side_effect=RuntimeError("Auth DB offline")))
    record_chat_turn(
        thread_id="th_001",
        erp_id="202101001",
        role="student",
        user_message="Hello",
        assistant_message="Hi there!",
        trace_id="tr_turn_1",
    )
