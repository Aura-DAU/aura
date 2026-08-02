# Shared PostgreSQL connection pool for the AURA Auth DB.
# Import `get_conn` anywhere that needs a DB connection.
# AUTH_DB_URL=postgresql://aura_app:<password>@localhost:5432/aura_auth

import os
import time
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager
from typing import Optional

_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

# Fix DB-RETRY: query()/execute() previously had zero retry tolerance — any
# transient connection-level hiccup (pool momentarily exhausted, a stale
# connection dropped by the server) raised immediately. Personal-data
# queries chain several sequential DB round trips per request
# (get_student_profile, access-gate lookups, audit_log) through this same
# small 10-connection pool, so they hit this far more often than pure-RAG
# queries (which mostly go to Qdrant, not Postgres) — surfacing as the
# generic, unhelpful "Sorry, I encountered an error while generating a
# response" message specifically on personal questions. A couple of quick
# retries with a short backoff absorbs exactly that class of failure without
# masking genuine, persistent DB problems (which still raise after retries
# are exhausted) or ever retrying a real SQL/data error (see the isinstance
# check below — only psycopg2's own connection-level exceptions qualify).
_RETRYABLE_ERRORS = (
    psycopg2.OperationalError,
    psycopg2.pool.PoolError,
    psycopg2.InterfaceError,
)
_MAX_RETRIES = 2
_RETRY_BACKOFF_SECONDS = 0.2


def _with_retries(fn):
    last_err = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            return fn()
        except _RETRYABLE_ERRORS as e:
            last_err = e
            global _pool
            if isinstance(e, (psycopg2.pool.PoolError, psycopg2.InterfaceError)):
                # A dead/exhausted pool won't self-heal by retrying against
                # the same handle — force a fresh pool on the next attempt.
                _pool = None
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            raise
    raise last_err  # pragma: no cover — unreachable, satisfies linters


def _init_pool() -> psycopg2.pool.ThreadedConnectionPool:
    url = os.environ.get("AUTH_DB_URL")
    if not url:
        raise RuntimeError(
            "AUTH_DB_URL environment variable is not set. "
            "Set it to a PostgreSQL connection string, e.g. "
            "postgresql://aura_app:pass@localhost:5432/aura_auth"
        )
    return psycopg2.pool.ThreadedConnectionPool(
        minconn=2, maxconn=10, dsn=url,
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def pool() -> psycopg2.pool.ThreadedConnectionPool:
    global _pool
    if _pool is None:
        _pool = _init_pool()
    return _pool


@contextmanager
def get_conn():
    # Context manager that checks out a connection from the pool,
    # commits on clean exit, rolls back on exception, returns to pool.
    p = pool()
    conn = p.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        p.putconn(conn)


def query(sql: str, params: tuple = ()) -> list[dict]:
    # One-shot query helper — use for reads.
    # Enforces SELECT-only statement execution at the code level.
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(
            "db_conn.query only accepts SELECT statements. "
            f"Received: {sql[:40]!r}"
        )

    def _run():
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                return [dict(r) for r in cur.fetchall()]

    return _with_retries(_run)


def execute(sql: str, params: tuple = ()) -> None:
    # One-shot execute helper — use for writes.
    def _run():
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)

    return _with_retries(_run)
