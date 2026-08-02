"""Admission-control / load-shedding tests for the chat endpoints.

Verifies that when every concurrency slot is taken, a new request waits only up
to CHAT_QUEUE_WAIT_TIMEOUT and is then rejected with a retryable 503 — instead
of queueing unbounded — and that the slot is always released on exit.
"""

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.routes import chat_routes


def test_acquire_chat_slot_sheds_load_with_retryable_503(monkeypatch):
    sem = asyncio.Semaphore(1)
    monkeypatch.setattr(chat_routes, "chat_queue_lock", sem)
    monkeypatch.setattr(chat_routes, "CHAT_QUEUE_WAIT_TIMEOUT", 0.01)

    async def scenario():
        await sem.acquire()  # occupy the only slot → next acquire must wait
        with pytest.raises(HTTPException) as excinfo:
            await chat_routes._acquire_chat_slot()
        return excinfo.value

    exc = asyncio.run(scenario())
    assert exc.status_code == 503
    assert exc.headers.get("Retry-After") == "5"


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
