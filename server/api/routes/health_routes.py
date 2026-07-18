# Health probes — public /health; admin-only /health/detail.
import os

from fastapi import APIRouter, Depends, HTTPException

from api.auth import Identity, require_identity

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    # Public liveness only — no secrets or env detail.
    return {"status": "online", "service": "AURA API"}


@router.get("/health/detail")
async def health_detail(identity: Identity = Depends(require_identity)):
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "INTERNAL_JWT_SECRET": bool(os.getenv("INTERNAL_JWT_SECRET")),
        "AUTH_DB_URL": bool(os.getenv("AUTH_DB_URL")),
        "ERP_DB_HOST": bool(os.getenv("ERP_DB_HOST")),
    }
