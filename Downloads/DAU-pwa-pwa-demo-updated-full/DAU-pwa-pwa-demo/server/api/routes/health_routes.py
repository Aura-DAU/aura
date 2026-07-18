"""
Health check routes — GET /health, GET /health/detail

Extracted from api.py to keep routes modular per CLAUDE.md.

/health       — public liveness probe (no auth). Checks all critical dependencies.
/health/detail — admin-only detail view (env var presence, dependency status).
"""
import os

from fastapi import APIRouter, Depends, HTTPException

from api.auth import require_identity, Identity

router = APIRouter()


def _check_redis() -> dict:
    """Ping Redis and return status."""
    try:
        import redis as _redis
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        client = _redis.from_url(url, socket_connect_timeout=2)
        client.ping()
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_postgres() -> dict:
    """Run a trivial SELECT against the auth DB and return status."""
    try:
        from db.connection import execute  # noqa: PLC0415
        execute("SELECT 1")
        return {"status": "ok"}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


def _check_pinecone() -> dict:
    """Verify Pinecone credentials are present (connectivity check is deferred
    to avoid cold-start latency on every /health call)."""
    api_key = os.getenv("PINECONE_API_KEY")
    index   = os.getenv("PINECONE_INDEX")
    if api_key and index:
        return {"status": "configured"}
    return {"status": "misconfigured", "detail": "PINECONE_API_KEY or PINECONE_INDEX not set"}


@router.get("/health")
async def health():
    """Public liveness probe. Returns degraded status if any dependency is down."""
    redis_status    = _check_redis()
    postgres_status = _check_postgres()
    pinecone_status = _check_pinecone()

    all_ok = (
        redis_status["status"] == "ok"
        and postgres_status["status"] == "ok"
        and pinecone_status["status"] in ("ok", "configured")
    )

    return {
        "status":   "online" if all_ok else "degraded",
        "service":  "AURA API",
        "dependencies": {
            "redis":    redis_status,
            "postgres": postgres_status,
            "pinecone": pinecone_status,
        },
    }


@router.get("/health/detail")
async def health_detail(identity: Identity = Depends(require_identity)):
    """Admin-only detailed health view: env var presence + dependency pings."""
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        "env": {
            "INTERNAL_JWT_SECRET":    bool(os.getenv("INTERNAL_JWT_SECRET")),
            "AUTH_DB_URL":            bool(os.getenv("AUTH_DB_URL")),
            "ERP_DB_HOST":            bool(os.getenv("ERP_DB_HOST")),
            "PINECONE_API_KEY":       bool(os.getenv("PINECONE_API_KEY")),
            "GROQ_API_KEY":           bool(os.getenv("GROQ_API_KEY")),
            "REDIS_URL":              bool(os.getenv("REDIS_URL")),
        },
        "dependencies": {
            "redis":    _check_redis(),
            "postgres": _check_postgres(),
            "pinecone": _check_pinecone(),
        },
    }
