"""
Google Calendar routes — slot viewing and OAuth connect/disconnect.

GET  /calendar/slots/{faculty_erp_id}?date=YYYY-MM-DD
     Students see available slots for a specific faculty on a given day.
     Access: student must be enrolled in the faculty's course OR be their BTP mentee.

GET  /calendar/connect
     Starts the Google OAuth 2.0 authorization code flow for the requesting faculty.

GET  /calendar/callback?code=...&state=...
     OAuth callback — exchanges the auth code for tokens, stores in vault.

DELETE /calendar/disconnect
     Faculty unlinks their Google Calendar from AURA.

GET  /calendar/status
     Returns whether the requesting faculty has linked their calendar.
"""

import os
import datetime
import urllib.parse
import jwt

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse

from api.auth import require_identity, Identity, get_internal_jwt_secret, ALGORITHM
from pipeline.google_calendar.slot_service import get_available_slots
from pipeline.google_calendar.token_vault import (
    store_tokens, unlink_calendar, is_linked, has_write_scope, CalendarNotLinked,
    SCOPE_READONLY, SCOPE_EVENTS,
)
from pipeline.google_calendar import timetable_sync
from pipeline.google_calendar.writer import unsync_all

router = APIRouter(prefix="/calendar", tags=["calendar"])

GOOGLE_AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL   = "https://oauth2.googleapis.com/token"
CLIENT_ID          = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
CLIENT_SECRET      = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
REDIRECT_URI       = os.environ.get(
    "GOOGLE_CALENDAR_REDIRECT_URI",
    "https://aura.dau.ac.in/api/calendar/callback",
)
CALENDAR_SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_SCOPE_EVENTS   = "https://www.googleapis.com/auth/calendar.events"

def _frontend_origin() -> str:
    return os.environ.get("PROD_FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")


@router.get("/slots/{faculty_erp_id}")
def get_faculty_slots(
    faculty_erp_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    identity: Identity = Depends(require_identity),
):
    """
    View available booking slots for a faculty member.
    Students: only for faculty in their enrolled courses or BTP guide.
    Faculty: can view own slots or any colleague's slots.
    """
    # Basic parse/validate the date
    try:
        target_date = datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD format")

    # Authorization: if student, confirm they have a relationship with this faculty
    if identity.role == "student":
        # Lazy import to avoid circular at top level
        from erp_connector import ERPConnector
        erp = ERPConnector()
        shared = erp.get_shared_courses(faculty_erp_id, identity.erp_id)
        btp    = erp.get_btp_students(faculty_erp_id)
        btp_rolls = [b["student_roll"] for b in btp]
        if not shared and identity.erp_id not in btp_rolls:
            raise HTTPException(
                status_code=403,
                detail="You can only view slots for faculty in your enrolled courses or your BTP guide.",
            )

    return get_available_slots(faculty_erp_id, target_date)


@router.get("/connect")
def start_calendar_oauth(identity: Identity = Depends(require_identity)):
    """Start Google Calendar OAuth flow. Faculty get readonly scope,
    students get events (read/write) scope for timetable sync."""
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Only students and faculty can connect a Google Calendar.")
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CALENDAR_CLIENT_ID not configured.")
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    # Mint a short-lived signed state token containing the erp_id and role
    state_payload = {
        "erp_id": identity.erp_id,
        "role": identity.role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    }
    state_token = jwt.encode(state_payload, secret, algorithm=ALGORITHM)

    # Students need write scope for timetable sync; faculty need readonly
    scope = CALENDAR_SCOPE_EVENTS if identity.role == "student" else CALENDAR_SCOPE_READONLY

    params = {
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         scope,
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state_token,
    }
    auth_url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def calendar_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),  # signed JWT state token
):
    """
    OAuth callback. Exchanges auth code for tokens and stores them.
    This endpoint is called by Google's OAuth server — it is NOT
    called by the frontend directly.
    """
    import requests
    import datetime

    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured on the server.")

    # Cryptographically verify the state parameter to prevent CSRF / Account Link Hijacking
    try:
        claims = jwt.decode(state, secret, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="State token expired. Please reconnect calendar.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid state token. Possible CSRF attempt.")

    erp_id = claims.get("erp_id")
    if not erp_id:
        raise HTTPException(status_code=400, detail="State token payload is missing erp_id.")

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }, timeout=10)
    if not resp.ok:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

    data          = resp.json()
    access_token  = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in    = data.get("expires_in", 3600)
    expiry        = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token returned. Ensure prompt=consent and access_type=offline in the auth URL.",
        )

    # Determine scope from the role stored in state
    role = claims.get("role", "faculty")
    scope = SCOPE_EVENTS if role == "student" else SCOPE_READONLY

    store_tokens(erp_id=erp_id, access_token=access_token,
                 refresh_token=refresh_token, token_expiry=expiry,
                 scope=scope)

    return RedirectResponse(url=f"{_frontend_origin()}/dashboard?calendar=connected")


@router.delete("/disconnect")
def disconnect_calendar(identity: Identity = Depends(require_identity)):
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Only students and faculty can disconnect a calendar.")
    if identity.role == "student":
        # Must remove every event AURA created BEFORE dropping the token —
        # once the token is gone we lose the only credential that can
        # delete them, so skipping this orphans real events on the
        # student's Google Calendar forever.
        unsync_all(identity.erp_id)
    unlink_calendar(identity.erp_id)
    return {"status": "disconnected"}


@router.get("/status")
def calendar_status(identity: Identity = Depends(require_identity)):
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Calendar status is only available for students and faculty.")
    linked = is_linked(identity.erp_id)
    payload = {"linked": linked, "erp_id": identity.erp_id}
    if identity.role == "student":
        # Must check the actual granted scope, not just "linked" — a
        # faculty-style readonly grant (or any non-write grant) is linked
        # but cannot sync. The frontend trusts this flag as-is.
        payload["can_sync_timetable"] = linked and has_write_scope(identity.erp_id)
    return payload


# -- Timetable sync (student write flow) --------------------------------------


@router.post("/timetable/sync")
def sync_timetable_to_calendar(identity: Identity = Depends(require_identity)):
    """Sync the student's AURA timetable to their Google Calendar."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can sync a timetable to Google Calendar.")
    # timetable_sync.apply() reports failures via a status field rather than
    # raising, so they must be checked explicitly — otherwise a
    # "calendar_not_connected" or "error" result silently comes back as a
    # 200 OK and the frontend has no way to tell it wasn't a success.
    result = timetable_sync.apply(identity)
    if result["status"] == "calendar_not_connected":
        raise HTTPException(status_code=409, detail=result.get("message", "Google Calendar is not connected."))
    if result["status"] == "error":
        raise HTTPException(status_code=409, detail=result.get("message", "Could not sync timetable."))
    return result


@router.delete("/timetable/sync")
def unsync_timetable_from_calendar(identity: Identity = Depends(require_identity)):
    """Remove all AURA-created events from the student's Google Calendar,
    without disconnecting the calendar link itself (so they can re-sync
    later without going through OAuth consent again)."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can unsync a timetable from Google Calendar.")
    return timetable_sync.unsync(identity)