"""db.connection.pool() lazy-init race fix: a burst of concurrent first
callers must build exactly one ThreadedConnectionPool, not one per racing
thread, and the pool size must be env-tunable."""

import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

SERVER_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SERVER_DIR))

import pytest

from db import connection as db_conn


@pytest.fixture(autouse=True)
def _isolate_pool(monkeypatch):
    monkeypatch.setattr(db_conn, "_pool", None)
    monkeypatch.setenv("AUTH_DB_URL", "postgresql://user:pass@localhost:5432/testdb")
    yield
    monkeypatch.setattr(db_conn, "_pool", None)


def test_pool_built_exactly_once_under_concurrent_first_callers(monkeypatch):
    build_calls = []

    class FakePool:
        def __init__(self, **kwargs):
            build_calls.append(kwargs)
            time.sleep(0.05)  # widen the race window the lock must close

    monkeypatch.setattr(db_conn.psycopg2.pool, "ThreadedConnectionPool", FakePool)

    results = []
    threads = [
        threading.Thread(target=lambda: results.append(db_conn.pool()))
        for _ in range(10)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(build_calls) == 1, "the pool must be built exactly once, not once per racing thread"
    assert len({id(r) for r in results}) == 1, "every caller must get the same pool object"


def test_pool_size_is_env_tunable_defaults_unchanged(monkeypatch):
    captured = {}

    class FakePool:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(db_conn.psycopg2.pool, "ThreadedConnectionPool", FakePool)

    db_conn.pool()
    assert captured["minconn"] == 2 and captured["maxconn"] == 10  # unchanged defaults


def test_pool_size_env_override(monkeypatch):
    monkeypatch.setenv("AUTH_DB_POOL_MIN", "5")
    monkeypatch.setenv("AUTH_DB_POOL_MAX", "40")
    monkeypatch.setattr(db_conn, "AUTH_DB_POOL_MIN", 5)
    monkeypatch.setattr(db_conn, "AUTH_DB_POOL_MAX", 40)
    captured = {}

    class FakePool:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(db_conn.psycopg2.pool, "ThreadedConnectionPool", FakePool)

    db_conn.pool()
    assert captured["minconn"] == 5 and captured["maxconn"] == 40


def test_already_built_pool_never_touches_the_lock(monkeypatch):
    sentinel = object()
    monkeypatch.setattr(db_conn, "_pool", sentinel)
    monkeypatch.setattr(db_conn, "_pool_lock", SimpleNamespace(
        __enter__=lambda *a: pytest.fail("lock must not be entered on the fast path"),
        __exit__=lambda *a: None,
    ))
    assert db_conn.pool() is sentinel
