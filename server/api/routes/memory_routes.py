# DELETE /memory/thread/{thread_id} — drop one conversation's persistent block.
# DELETE /memory — drop everything this identity has stored.
#
# "Clear chat" in the UI has to mean deletion: without this, a cleared thread's
# block stayed in Redis for REDIS_USER_MEMORY_TTL_SECONDS (90 days by default)
# and kept being injected into later conversations. Called by the Next.js proxy
# at aura/app/api/chat/memory/route.ts.
import logging

from fastapi import APIRouter, Depends, Path

from api.auth import Identity, require_identity
from pipeline.memory.user_memory import get_user_memory_store

router = APIRouter(prefix="/memory", tags=["memory"])
logger = logging.getLogger(__name__)


@router.delete("/thread/{thread_id}")
async def delete_thread_memory(
    thread_id: str = Path(..., min_length=1, max_length=64),
    identity: Identity = Depends(require_identity),
):
    # Guests have no stored memory at all (_identity_key returns None), so the
    # store no-ops and this stays a successful, idempotent 200.
    deleted = get_user_memory_store().delete(identity.as_dict(), thread_id)
    return {"ok": True, "deleted": deleted}


@router.delete("")
async def delete_all_memory(identity: Identity = Depends(require_identity)):
    deleted = get_user_memory_store().delete_all(identity.as_dict())
    return {"ok": True, "deleted": deleted}
