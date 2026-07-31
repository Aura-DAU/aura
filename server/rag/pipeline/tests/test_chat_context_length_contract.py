"""A context-window overflow must never reach the client as an HTTP 500.

The generation stage already degrades in-pipeline (AURA-CTX-001 →
CONTEXT_LENGTH_ANSWER), but `_ask_with_memory` calls several collaborators the
route does not guard, and `/chat` only catches `ChatAdmissionShed`. Anything
else — a `ContextLengthExceeded` from the memory/budget layer, or a
`RAGPipelineError` wrapping a vLLM 400 — escaped to Starlette and became an
opaque 500 with no code the frontend or an operator could act on.

These tests drive the real route through a FastAPI app with a signed internal
JWT so the assertion is on the wire status, not on an internal return value.
"""

import datetime as dt
import sys
from pathlib import Path
from unittest.mock import patch

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.auth import (
    ALGORITHM,
    INTERNAL_JWT_AUDIENCE,
    INTERNAL_JWT_ISSUER,
    get_internal_jwt_secret,
)
from api.routes import chat_routes
from pipeline.exceptions import ContextLengthExceeded, RAGPipelineError
from pipeline.memory.user_memory import (
    InMemoryUserMemoryStore,
    reset_user_memory_store_for_tests,
)

CTX_STATS = {
    "max_model_len": 8192,
    "reserved_output": 2048,
    "total_input": 6145,
    "fit": False,
}


def _token(role: str = "student", erp_id: str = "202401001") -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return jwt.encode(
        {
            "erpId": erp_id,
            "role": role,
            "iat": now,
            "exp": now + dt.timedelta(minutes=15),
            "iss": INTERNAL_JWT_ISSUER,
            "aud": INTERNAL_JWT_AUDIENCE,
        },
        get_internal_jwt_secret(),
        algorithm=ALGORITHM,
    )


def _auth(role: str = "student", erp_id: str = "202401001") -> dict:
    return {"Authorization": f"Bearer {_token(role, erp_id)}"}


class _ExplodingAura:
    def __init__(self, exc: Exception):
        self._exc = exc

    def ask(self, **_kwargs):
        raise self._exc


@pytest.fixture
def client():
    reset_user_memory_store_for_tests(InMemoryUserMemoryStore())
    app = FastAPI()
    app.include_router(chat_routes.router)
    # raise_server_exceptions=False so an unhandled error surfaces as the 500
    # the browser would actually receive instead of re-raising into the test.
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    reset_user_memory_store_for_tests()


@pytest.fixture(autouse=True)
def _unlimited_quota():
    with patch.object(chat_routes, "enforce_quota", return_value=None):
        yield


def _post(client, question: str = "Summarise the whole B.Tech ICT curriculum."):
    return client.post("/chat", json={"question": question}, headers=_auth())


def test_context_length_overflow_is_413_not_500(client):
    with patch.object(
        chat_routes,
        "get_aura",
        return_value=_ExplodingAura(ContextLengthExceeded(stats=CTX_STATS)),
    ):
        res = _post(client)

    assert res.status_code != 500, "context overflow must never be an opaque 500"
    assert res.status_code == 413
    body = res.json()
    assert body["code"] == "AURA-CTX-001"
    assert body["detail"]
    # Flat shape, same keys the admission shed returns — not FastAPI-nested.
    assert set(body) >= {"detail", "code"}


def test_wrapped_vllm_400_is_413_not_500(client):
    """inference_router wraps the SDK 400; the wrapper must still be attributed."""
    wrapped = RAGPipelineError(
        "API request failed with unretryable status 400: This model's maximum "
        "context length is 8192 tokens. However, you requested 8193 tokens "
        "(6145 in the messages, 2048 in the completion). Please reduce the "
        "length of the messages or completion."
    )
    with patch.object(chat_routes, "get_aura", return_value=_ExplodingAura(wrapped)):
        res = _post(client)

    assert res.status_code == 413
    assert res.json()["code"] == "AURA-CTX-001"


def test_generic_pipeline_error_is_a_retryable_503_not_500(client):
    exc = RAGPipelineError("All vLLM inference nodes exhausted after 5 attempts")
    with patch.object(chat_routes, "get_aura", return_value=_ExplodingAura(exc)):
        res = _post(client)

    assert res.status_code == 503
    body = res.json()
    assert body["code"] == "RAG_PIPELINE_ERROR"
    assert body["retryAfter"] == chat_routes.CHAT_RETRY_AFTER_SECONDS
    assert res.headers.get("Retry-After") == str(chat_routes.CHAT_RETRY_AFTER_SECONDS)


def test_pipeline_error_releases_the_admission_slot(client):
    exc = ContextLengthExceeded(stats=CTX_STATS)
    before = chat_routes.chat_queue_lock._value
    with patch.object(chat_routes, "get_aura", return_value=_ExplodingAura(exc)):
        _post(client)
    assert chat_routes.chat_queue_lock._value == before


def test_streaming_context_overflow_is_attributed_not_generic(client):
    """The SSE surface stays a 200 stream, but must carry AURA-CTX-001."""
    exc = ContextLengthExceeded(stats=CTX_STATS)
    with patch.object(chat_routes, "get_aura", return_value=_ExplodingAura(exc)):
        res = client.post(
            "/chat/stream",
            json={"question": "Summarise everything."},
            headers=_auth(),
        )

    assert res.status_code == 200
    body = res.text
    assert '"code": "AURA-CTX-001"' in body
    assert "data: [DONE]" in body
