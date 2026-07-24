# Google Calendar slots + OAuth connect/callback/disconnect/status.
import datetime
import os
import urllib.parse

import jwt
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import RedirectResponse

from api.auth import (
    ALGORITHM,
    GCAL_OAUTH_STATE_AUDIENCE,
    GCAL_OAUTH_STATE_ISSUER,
    GCAL_OAUTH_STATE_TYP,
    Identity,
    get_internal_jwt_secret,
    require_identity,
)
from pipeline.google_calendar.slot_service import get_available_slots
from pipeline.google_calendar.token_vault import is_linked, store_tokens, unlink_calendar

router = APIRouter(prefix="/calendar", tags=["calendar"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CLIENT_ID = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get(
    "GOOGLE_CALENDAR_REDIRECT_URI",
    # Callback lives on FastAPI (proxied at /backend/calendar/callback). There is
    # no Next.js /api/calendar BFF route.
    "https://aura.daiict.ac.in/backend/calendar/callback",
)
CALENDAR_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"


def _frontend_origin() -> str:
    return os.environ.get("PROD_FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")


@router.get("/slots/{faculty_erp_id}")
def get_faculty_slots(
    faculty_erp_id: str = Path(..., min_length=1, max_length=64),
    date: str = Query(..., min_length=10, max_length=10, description="Date in YYYY-MM-DD format"),
    identity: Identity = Depends(require_identity),
):
    # Students: enrolled course or BTP mentee only; faculty can view colleagues.
    try:
        target_date = datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD format")

    if identity.role == "student":
        from erp_connector import ERPConnector
        erp = ERPConnector()
        shared = erp.get_shared_courses(faculty_erp_id, identity.erp_id)
        btp = erp.get_btp_students(faculty_erp_id)
        btp_rolls = [b["student_roll"] for b in btp]
        if not shared and identity.erp_id not in btp_rolls:
            raise HTTPException(
                status_code=403,
                detail="You can only view slots for faculty in your enrolled courses or your BTP guide.",
            )

    return get_available_slots(faculty_erp_id, target_date)


@router.get("/connect")
def start_calendar_oauth(identity: Identity = Depends(require_identity)):
    # Faculty-only OAuth start; state is a short-lived signed JWT (CSRF).
    if identity.role != "faculty":
        raise HTTPException(status_code=403, detail="Only faculty can connect a Google Calendar.")
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CALENDAR_CLIENT_ID not configured.")
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    state_payload = {
        "erp_id": identity.erp_id,
        "typ": GCAL_OAUTH_STATE_TYP,
        "iss": GCAL_OAUTH_STATE_ISSUER,
        "aud": GCAL_OAUTH_STATE_AUDIENCE,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
    }
    state_token = jwt.encode(state_payload, secret, algorithm=ALGORITHM)

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": CALENDAR_SCOPE,
        "access_type": "offline",
        "prompt": "consent",
        "state": state_token,
    }
    auth_url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
def calendar_oauth_callback(
    code: str = Query(..., min_length=1, max_length=2048),
    state: str = Query(..., min_length=1, max_length=4096),
):
    # Google OAuth callback — exchange code, store tokens, redirect to dashboard.
    import requests

    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured on the server.")

    try:
        claims = jwt.decode(
            state,
            secret,
            algorithms=[ALGORITHM],
            audience=GCAL_OAUTH_STATE_AUDIENCE,
            issuer=GCAL_OAUTH_STATE_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="State token expired. Please reconnect calendar.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid state token. Possible CSRF attempt.")

    if claims.get("typ") != GCAL_OAUTH_STATE_TYP:
        raise HTTPException(status_code=400, detail="Invalid state token. Possible CSRF attempt.")

    erp_id = claims.get("erp_id")
    if not erp_id:
        raise HTTPException(status_code=400, detail="State token payload is missing erp_id.")

    resp = requests.post(GOOGLE_TOKEN_URL, data={
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }, timeout=10)
    if not resp.ok:
        print(f"[calendar] token exchange failed: {resp.status_code} {resp.text[:500]}")
        raise HTTPException(status_code=400, detail="Calendar authorization failed. Please try again.")

    data = resp.json()
    access_token = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in", 3600)
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token returned. Ensure prompt=consent and access_type=offline in the auth URL.",
        )

    store_tokens(
        erp_id=erp_id,
        access_token=access_token,
        refresh_token=refresh_token,
        token_expiry=expiry,
    )

    return RedirectResponse(url=f"{_frontend_origin()}/dashboard?calendar=connected")


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
