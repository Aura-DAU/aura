# eCampus vault link/unlink/status — students only (not auth endpoints).
from fastapi import APIRouter, Depends, HTTPException

from api.auth import Identity, require_identity
from api.schemas import LinkEcampusRequest
from pipeline.ecampus.credentials_vault import is_linked, store_credentials, unlink_credentials

router = APIRouter(prefix="/ecampus", tags=["ecampus"])


@router.post("/link")
def link_ecampus(
    request: LinkEcampusRequest,
    identity: Identity = Depends(require_identity),
):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can link an eCampus account.")
    store_credentials(identity.erp_id, request.ecampus_username, request.ecampus_password)
    return {"status": "linked"}


@router.delete("/link")
def unlink_ecampus(identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can unlink.")
    unlink_credentials(identity.erp_id)
    return {"status": "unlinked"}


@router.get("/link")
def ecampus_link_status(identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a link status.")
    return {"linked": is_linked(identity.erp_id)}
