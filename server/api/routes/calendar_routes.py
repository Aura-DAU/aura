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

from api.auth import require_identity, Identity
from pipeline.google_calendar.slot_service import get_available_slots
from pipeline.google_calendar.token_vault import (
    store_tokens, unlink_calendar, is_linked, CalendarNotLinked
)

def get_internal_jwt_secret() -> str:
    return os.environ.get("INTERNAL_JWT_SECRET", "")
ALGORITHM           = "HS256"

router = APIRouter(prefix="/calendar", tags=["calendar"])

GOOGLE_AUTH_URL    = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL   = "https://oauth2.googleapis.com/token"
CLIENT_ID          = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
CLIENT_SECRET      = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
REDIRECT_URI       = os.environ.get(
    "GOOGLE_CALENDAR_REDIRECT_URI",
    "https://aura.dau.ac.in/api/calendar/callback",
)
CALENDAR_SCOPE     = "https://www.googleapis.com/auth/calendar.readonly"


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
    """Start Google Calendar OAuth flow. Faculty only."""
    if identity.role != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can connect a Google Calendar.")
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CALENDAR_CLIENT_ID not configured.")
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    # Mint a short-lived signed state token containing the faculty erp_id to prevent CSRF / State Injection
    state_payload = {
        "erp_id": identity.erp_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    }
    state_token = jwt.encode(state_payload, secret, algorithm=ALGORITHM)

    params = {
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "response_type": "code",
        "scope":         CALENDAR_SCOPE,
        "access_type":   "offline",   # needed to get refresh_token
        "prompt":        "consent",
        "state":         state_token, # signed token prevents tampering
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

    store_tokens(erp_id=erp_id, access_token=access_token,
                 refresh_token=refresh_token, token_expiry=expiry)

    # Redirect back to the faculty dashboard
    return RedirectResponse(url="/calendar/connected")


@router.delete("/disconnect")
def disconnect_calendar(identity: Identity = Depends(require_identity)):
    if identity.role != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can disconnect a calendar.")
    unlink_calendar(identity.erp_id)
    return {"status": "disconnected"}


@router.get("/status")
def calendar_status(identity: Identity = Depends(require_identity)):
    if identity.role != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty have a calendar link status.")
    return {"linked": is_linked(identity.erp_id), "erp_id": identity.erp_id}