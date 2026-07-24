"""
timetable_routes.py — direct (non-chat) endpoints for the dashboard.

The dashboard's timetable card calls GET /timetable/me directly (not through
the chat pipeline) so it renders instantly on login. Editing the timetable,
by contrast, only happens conversationally through the agent tools in
pipeline.timetable.tool_registry (update_my_timetable / undo_timetable_change)
— there is deliberately no PATCH/PUT endpoint here, so every change to a
student's timetable goes through the confirm-before-write agent flow and
gets a natural-language record of *why* the student wanted it changed.

Also exposes the Web Push subscribe/unsubscribe endpoints used by the "class
in 10 minutes" reminder feature.
"""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

import db.connection as db_conn
from api.auth import require_identity, Identity
from pipeline.timetable import service
from pipeline.timetable.service import TimetableError

router = APIRouter(prefix="/timetable", tags=["timetable"])
push_router = APIRouter(prefix="/push", tags=["push"])


@router.get("/me")
def get_my_timetable(identity: Identity = Depends(require_identity)):
    """Student's own effective timetable — cohort master merged with their
    personal overrides. Used by the dashboard's timetable card."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        return service.get_effective_timetable(identity)
    except TimetableError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/me/changes")
def get_my_timetable_changes(identity: Identity = Depends(require_identity)):
    """List of the student's own personal edits, for a small 'your changes' list in the UI."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a personal timetable.")
    try:
        return {"changes": service.list_my_changes(identity)}
    except TimetableError as e:
        raise HTTPException(status_code=409, detail=str(e))


class ElectiveSelectionsIn(BaseModel):
    course_codes: list[str]


@router.get("/electives")
def get_electives(identity: Identity = Depends(require_identity)):
    """Available elective courses for the student's own cohort (year + sem),
    with a `selected` flag for each. See service.get_available_electives —
    scoped so a student never sees electives offered to a different
    year/semester."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have elective selections.")
    try:
        return service.get_available_electives(identity)
    except TimetableError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/electives")
def post_electives(body: ElectiveSelectionsIn, identity: Identity = Depends(require_identity)):
    """Save the student's elective course selections — resolved against
    their own cohort only (see service.save_elective_selections)."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have elective selections.")
    try:
        return service.save_elective_selections(identity, body.course_codes)
    except TimetableError as e:
        raise HTTPException(status_code=409, detail=str(e))


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionIn(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
    user_agent: str | None = None


@push_router.get("/vapid-public-key")
def get_vapid_public_key():
    """The frontend needs this to create a PushSubscription in the browser."""
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="Push notifications are not configured on this server yet.")
    return {"publicKey": key}


@push_router.post("/subscribe")
def subscribe_to_push(body: PushSubscriptionIn, identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can subscribe to timetable reminders.")

    existing = db_conn.query(
        "SELECT id FROM push_subscriptions WHERE endpoint = %s", (body.endpoint,)
    )
    if existing:
        db_conn.execute(
            """UPDATE push_subscriptions
               SET erp_id = %s, p256dh = %s, auth_key = %s, user_agent = %s,
                   is_active = TRUE, last_seen_at = now()
               WHERE endpoint = %s""",
            (identity.erp_id, body.keys.p256dh, body.keys.auth, body.user_agent, body.endpoint),
        )
    else:
        db_conn.execute(
            """INSERT INTO push_subscriptions (id, erp_id, endpoint, p256dh, auth_key, user_agent)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (str(uuid.uuid4()), identity.erp_id, body.endpoint, body.keys.p256dh, body.keys.auth, body.user_agent),
        )
    return {"status": "subscribed"}


@push_router.delete("/subscribe")
def unsubscribe_from_push(endpoint: str, identity: Identity = Depends(require_identity)):
    db_conn.execute(
        "UPDATE push_subscriptions SET is_active = FALSE WHERE endpoint = %s AND erp_id = %s",
        (endpoint, identity.erp_id),
    )
    return {"status": "unsubscribed"}
