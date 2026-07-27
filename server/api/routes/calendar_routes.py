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
from pipeline.google_calendar.token_vault import (
    store_tokens, unlink_calendar, is_linked, has_write_scope, CalendarNotLinked,
    SCOPE_READONLY, SCOPE_EVENTS,
)
from pipeline.google_calendar import timetable_sync
from pipeline.google_calendar.writer import unsync_all

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
CALENDAR_SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_SCOPE_EVENTS   = "https://www.googleapis.com/auth/calendar.events"

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
def start_calendar_oauth(
    identity: Identity = Depends(require_identity),
    return_to: str = Query(default="/dashboard", description="Path to redirect back to after OAuth completes"),
):
    """Start Google Calendar OAuth flow. Faculty get readonly scope,
    students get events (read/write) scope for timetable sync.

    Returns JSON {"url": "..."} so the frontend can navigate itself —
    fetch() does not follow cross-origin 307 redirects to Google.
    """
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Only students and faculty can connect a Google Calendar.")
    if not CLIENT_ID:
        raise HTTPException(status_code=500, detail="GOOGLE_CALENDAR_CLIENT_ID not configured.")
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    # Mint a short-lived signed state token containing the erp_id, role,
    # and the page to return to after consent so the callback can redirect
    # back to wherever the user started rather than always /dashboard.
    state_payload = {
        "erp_id":    identity.erp_id,
        "role":      identity.role,
        "return_to": return_to,
        "typ":       GCAL_OAUTH_STATE_TYP,
        "iss":       GCAL_OAUTH_STATE_ISSUER,
        "aud":       GCAL_OAUTH_STATE_AUDIENCE,
        "exp":       datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
    }
    state_token = jwt.encode(state_payload, secret, algorithm=ALGORITHM)

    # Students need write scope for timetable sync; faculty need readonly
    scope = CALENDAR_SCOPE_EVENTS if identity.role == "student" else CALENDAR_SCOPE_READONLY

    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope":         scope,
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state_token,
    }
    auth_url = GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)
    # Return the URL as JSON — the frontend navigates via window.location.href.
    # A 307 RedirectResponse cannot be followed by fetch() to an external
    # cross-origin URL (Google), so we give the URL to the client instead.
    return {"url": auth_url}


@router.get("/callback")
def calendar_oauth_callback(
    code: str = Query(..., min_length=1, max_length=2048),
    state: str = Query(..., min_length=1, max_length=4096),
):
    # Google OAuth callback — exchange code, store tokens, redirect back to
    # the page the user started the flow from (encoded in the state JWT).
    import requests

    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured on the server.")

    # Bug 9 fix: guard against missing credentials before hitting Google.
    if not CLIENT_ID or not CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google Calendar OAuth credentials (CLIENT_ID / CLIENT_SECRET) are not configured on the server.",
        )

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
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {resp.text}")

    data = resp.json()
    access_token  = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in = data.get("expires_in", 3600)
    expiry = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token returned. Ensure prompt=consent and access_type=offline in the auth URL.",
        )

    # Determine scope from the role stored in state
    role  = claims.get("role", "faculty")
    scope = SCOPE_EVENTS if role == "student" else SCOPE_READONLY

    store_tokens(erp_id=erp_id, access_token=access_token,
                 refresh_token=refresh_token, token_expiry=expiry,
                 scope=scope)

    # Bug 4 fix: redirect to the page the user started from, not always /dashboard.
    return_to = claims.get("return_to", "/dashboard").lstrip("/")
    return RedirectResponse(url=f"{_frontend_origin()}/{return_to}?calendar=connected")


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
