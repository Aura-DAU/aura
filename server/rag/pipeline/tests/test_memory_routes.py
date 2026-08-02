"""MEM-04 — clearing a chat must actually delete its persistent memory block.

Exercises the real route through a FastAPI app with a signed internal JWT, so a
regression that unregisters the router (or drops the store call) fails here
rather than silently leaving 90-day-retained memory behind.
"""

import datetime as dt
import sys
from pathlib import Path

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
from api.routes.memory_routes import router as memory_router
from pipeline.memory.user_memory import (
    InMemoryUserMemoryStore,
    reset_user_memory_store_for_tests,
)

STUDENT = {"role": "student", "erp_id": "202401001"}


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


@pytest.fixture
def client_and_store():
    store = InMemoryUserMemoryStore()
    reset_user_memory_store_for_tests(store)
    app = FastAPI()
    app.include_router(memory_router)
    with TestClient(app) as client:
        yield client, store
    reset_user_memory_store_for_tests()


def _auth(role: str = "student", erp_id: str = "202401001") -> dict:
    return {"Authorization": f"Bearer {_token(role, erp_id)}"}


def test_delete_thread_removes_only_that_conversation(client_and_store):
    client, store = client_and_store
    store.merge(STUDENT, "Asked about hostel fees.", thread_id="t1")
    store.merge(STUDENT, "Asked about elective clashes.", thread_id="t2")

    res = client.delete("/memory/thread/t1", headers=_auth())
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": True}

    remaining = store.get(STUDENT)
    assert "hostel fees" not in remaining
    assert "elective clashes" in remaining


def test_delete_thread_is_idempotent(client_and_store):
    client, _store = client_and_store
    res = client.delete("/memory/thread/never-existed", headers=_auth())
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": False}


def test_delete_all_clears_every_block(client_and_store):
    client, store = client_and_store
    store.merge(STUDENT, "One.", thread_id="t1")
    store.merge(STUDENT, "Two.", thread_id="t2")

    res = client.delete("/memory", headers=_auth())
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": True}
    assert store.get(STUDENT) == ""


def test_guest_delete_is_a_successful_noop(client_and_store):
    # Guests have no persistent memory by design — deleting must not 500.
    client, _store = client_and_store
    res = client.delete("/memory/thread/t1", headers=_auth(role="guest", erp_id="GUEST-1"))
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": False}


def test_delete_requires_authentication(client_and_store):
    client, store = client_and_store
    store.merge(STUDENT, "Private.", thread_id="t1")

    assert client.delete("/memory/thread/t1").status_code == 401
    # Another identity's token must not reach this user's blocks.
    other = _auth(erp_id="202409999")
    assert client.delete("/memory/thread/t1", headers=other).json()["deleted"] is False
    assert "Private." in store.get(STUDENT)
