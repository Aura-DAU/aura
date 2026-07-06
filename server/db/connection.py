"""
Shared PostgreSQL connection pool for the AURA Auth DB.
Import `get_conn` anywhere that needs a DB connection.

Connection string format:
  AUTH_DB_URL=postgresql://aura_app:<password>@localhost:5432/aura_auth
"""

import os
import psycopg2
import psycopg2.pool
import psycopg2.extras
from contextlib import contextmanager

_pool: psycopg2.pool.ThreadedConnectionPool | None = None


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
    """Context manager that checks out a connection from the pool,
    commits on clean exit, rolls back on exception, returns to pool."""
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
    """One-shot query helper — use for reads.
    Enforces SELECT-only statement execution at the code level."""
    if not sql.strip().upper().startswith("SELECT"):
        raise ValueError(
            "db_conn.query only accepts SELECT statements. "
            f"Received: {sql[:40]!r}"
        )
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]


def execute(sql: str, params: tuple = ()) -> None:
    """One-shot execute helper — use for writes."""
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
