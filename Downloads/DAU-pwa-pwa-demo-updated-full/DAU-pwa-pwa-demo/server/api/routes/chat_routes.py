"""
Chat route — POST /chat

Extracted from api.py to keep routes modular and under 300 lines per CLAUDE.md.
"""
import sys
import threading
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from api.auth import require_identity, Identity
from pipeline.rate_limiter import enforce_quota, QuotaExceeded

router = APIRouter()

# ── AURA singleton (shared with api.py via module-level state) ────────────
# Placed here so chat_routes.py doesn't need to import from api.py (circular).
_aura      = None
_aura_lock = threading.Lock()


def get_aura():
    global _aura
    if _aura is None:
        with _aura_lock:
            if _aura is None:
                server_dir = Path(__file__).resolve().parent.parent.parent
                rag_dir    = server_dir / "rag"
                for p in (str(server_dir), str(rag_dir)):
                    if p not in sys.path:
                        sys.path.insert(0, p)
                from rag import AURA  # noqa: PLC0415 — deferred heavy import
                _aura = AURA()
    return _aura


# ── Request models ────────────────────────────────────────────────────────
class HistoryTurn(BaseModel):
    role:    str
    content: str


class UserProfile(BaseModel):
    # Display/personalisation only — role and identity come from the
    # Next.js-minted internal JWT verified by require_identity(), never here.
    name:      Optional[str]       = None
    branch:    Optional[str]       = None
    year:      Optional[str]       = None
    semester:  Optional[str]       = None
    interests: Optional[str]       = None
    subjects:  Optional[List[str]] = None


class ChatRequest(BaseModel):
    question:       str
    history:        Optional[List[HistoryTurn]] = None
    userProfile:    Optional[UserProfile]       = None
    studentProfile: Optional[UserProfile]       = None

    def resolved_profile(self) -> Optional[UserProfile]:
        return self.studentProfile or self.userProfile


@router.post("/chat")
async def chat(
    request:  ChatRequest,
    identity: Identity = Depends(require_identity),
):
    history = [t.model_dump() for t in (request.history or [])][-6:]
    profile = request.resolved_profile()
    display_profile = profile.model_dump(exclude_none=True) if profile else None

    quota_key = identity.email or identity.erp_id
    try:
        enforce_quota(quota_key, identity.role)
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({exc.limit}/day).",
        ) from exc

    return await run_in_threadpool(
        get_aura().ask,
        question=request.question,
        history=history,
        identity=identity.as_dict(),
        display_profile=display_profile,
    )
