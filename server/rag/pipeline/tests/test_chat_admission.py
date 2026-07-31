"""Admission-control / load-shedding tests for the chat endpoints.

Verifies that when every concurrency slot is taken, a new request waits only up
to CHAT_QUEUE_WAIT_TIMEOUT and is then rejected with a retryable 503 — instead
of queueing unbounded — and that the slot is always released on exit.

Also locks in the EDGE-01 attribution contract: the backend shed must be
distinguishable from the edge's 429 (status, X-Aura-Shed-By, body code) and
must carry a Retry-After the frontend can act on.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.routes import chat_routes


def test_acquire_chat_slot_sheds_load_with_retryable_503(monkeypatch):
    sem = asyncio.Semaphore(1)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 0.01)

    async def scenario():
        await sem.acquire()  # occupy the only slot → next acquire must wait
        with pytest.raises(chat_routes.ChatAdmissionShed):
            await chat_routes._acquire_chat_slot()

    asyncio.run(scenario())


def test_admission_shed_response_shape_and_headers():
    """Flat JSON matching the edge @aura_shed body; distinguishable by status/code."""
    response = chat_routes._admission_shed_response()
    assert response.status_code == 503
    assert response.headers.get("Retry-After") == str(chat_routes.CHAT_RETRY_AFTER_SECONDS)
    assert response.headers.get("X-Aura-Shed-By") == "backend"
    assert response.headers.get("Cache-Control") == "no-store"

    body = json.loads(bytes(response.body).decode())
    assert body["code"] == "ADMISSION_OVERLOADED"
    assert body["shedBy"] == "backend"
    assert body["retryAfter"] == chat_routes.CHAT_RETRY_AFTER_SECONDS
    assert "retry" in body["detail"].lower()
    # Top-level flat shape — same keys the edge returns (not FastAPI-nested).
    assert set(body) >= {"detail", "code", "shedBy", "retryAfter"}


def test_acquire_chat_slot_logs_backend_attribution(monkeypatch, caplog):
    sem = asyncio.Semaphore(1)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 0.01)

    async def scenario():
        await sem.acquire()
        with pytest.raises(chat_routes.ChatAdmissionShed):
            await chat_routes._acquire_chat_slot()

    with caplog.at_level(logging.WARNING, logger=chat_routes.logger.name):
        asyncio.run(scenario())

    assert any(
        "chat_admission_shed" in record.getMessage()
        and "shed_by=backend" in record.getMessage()
        for record in caplog.records
    ), "shed must leave a greppable log line attributing the backend layer"


def test_chat_slot_acquires_and_releases(monkeypatch):
    sem = asyncio.Semaphore(2)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 1.0)

    async def scenario():
        async with chat_routes._chat_slot():
            taken = sem._value  # one slot consumed inside the context
        return taken, sem._value

    inside, after = asyncio.run(scenario())
    assert inside == 1  # slot held during the request
    assert after == 2   # slot returned to the pool on exit


def test_chat_slot_releases_even_when_body_raises(monkeypatch):
    sem = asyncio.Semaphore(1)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 1.0)

    async def scenario():
        with pytest.raises(ValueError):
            async with chat_routes._chat_slot():
                raise ValueError("boom")
        return sem._value

    assert asyncio.run(scenario()) == 1  # not leaked despite the error


def test_stream_slot_release_is_idempotent_under_cancel(monkeypatch):
    """Mirrors chat_stream's _release_slot: cancel must free the slot once,
    and a second release (outer finally) must not underflow the semaphore."""
    sem = asyncio.Semaphore(1)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 1.0)

    async def scenario():
        await chat_routes._acquire_chat_slot()
        slot_held = True

        def _release_slot() -> None:
            nonlocal slot_held
            if slot_held:
                slot_held = False
                chat_routes.chat_queue_lock.release()

        try:
            try:
                raise asyncio.CancelledError()
            except asyncio.CancelledError:
                _release_slot()
                # outer finally still runs in production
            finally:
                _release_slot()
        except asyncio.CancelledError:
            pass
        return sem._value

    assert asyncio.run(scenario()) == 1


def test_queue_wait_timeout_default_is_fast_shed():
    # Import from deps so the documented default for 1000-user bursts stays short.
    from api import deps

    assert deps.CHAT_QUEUE_WAIT_TIMEOUT <= 2.0 + 1e-9


def test_retry_after_constant_matches_edge():
    # Edge @aura_shed hardcodes Retry-After: 5. Keep the backend constant in
    # lockstep so the frontend can treat either shed with the same backoff.
    from api import deps

    assert deps.CHAT_RETRY_AFTER_SECONDS == 5
