"""
Admin routes — role_bindings management (SSO architecture).

Updated to use erp_id directly in role_bindings (no UUID user_id lookup).
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

import db.connection as db_conn
from api.auth import require_identity, Identity

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_BINDING_PREFIXES = (
    "class_advisor:",
    "course_instructor:",
    "dean_of_students",
    "exam_committee",
    "admin_full",
)


def _require_admin(identity: Identity = Depends(require_identity)) -> Identity:
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required.")
    return identity


def _check_erp_exists(erp_id: str) -> None:
    rows = db_conn.query(
        "SELECT 1 FROM user_identity_map WHERE erp_id = %s AND is_active = TRUE",
        (erp_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"No active user with erp_id '{erp_id}'.")


class AddBindingRequest(BaseModel):
    binding:    str
    expires_at: Optional[str] = None   # ISO-8601 or null = permanent


@router.get("/users/{erp_id}/bindings")
def list_bindings(erp_id: str, admin: Identity = Depends(_require_admin)):
    _check_erp_exists(erp_id)
    rows = db_conn.query(
        """SELECT id, binding, granted_at, expires_at, revoked
           FROM role_bindings WHERE erp_id = %s ORDER BY granted_at DESC""",
        (erp_id,),
    )
    return {"erp_id": erp_id, "bindings": [dict(r) for r in rows]}


@router.post("/users/{erp_id}/bindings")
def add_binding(
    erp_id: str,
    body:   AddBindingRequest,
    admin:  Identity = Depends(_require_admin),
):
    binding = body.binding.strip()
    if not any(binding.startswith(p) or binding == p for p in VALID_BINDING_PREFIXES):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid binding '{binding}'. Valid prefixes: {VALID_BINDING_PREFIXES}",
        )
    _check_erp_exists(erp_id)
    db_conn.execute(
        """INSERT INTO role_bindings (erp_id, binding, granted_by, expires_at)
           VALUES (%s, %s, %s, %s::timestamptz)""",
        (erp_id, binding, admin.erp_id, body.expires_at),
    )
    return {"status": "added", "erp_id": erp_id, "binding": binding}


@router.delete("/bindings/{binding_id}")
def revoke_binding(binding_id: int, admin: Identity = Depends(_require_admin)):
    rows = db_conn.query(
        "SELECT id FROM role_bindings WHERE id = %s AND revoked = FALSE",
        (binding_id,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Binding not found or already revoked.")
    db_conn.execute(
        "UPDATE role_bindings SET revoked = TRUE WHERE id = %s", (binding_id,)
    )
    return {"status": "revoked", "binding_id": binding_id}
