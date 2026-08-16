# Google Calendar OAuth + timetable sync routes.
#
# New endpoints added in this revision:
#   POST /calendar/timetable/sync         — async sync, returns job_id (202)
#   GET  /calendar/timetable/sync/status  — poll job status
#   DELETE /calendar/timetable/sync       — unsync (with ?keep_events=true option)
#   GET  /calendar/preferences            — get per-user preferences
#   PATCH /calendar/preferences           — update preferences (calendar, tz, policy, reminders)
#   GET  /calendar/calendars              — list user's Google Calendars
#   GET  /calendar/audit                  — sync audit log for this user
#   POST /calendar/timetable/sync/preview — preview what sync would create/update/delete

import datetime
import logging
import os
import urllib.parse

import jwt
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

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
    SCOPE_READONLY, SCOPE_EVENTS, get_preferences, update_preferences,
)
from pipeline.google_calendar import timetable_sync
from pipeline.google_calendar.writer import unsync_all
from pipeline.google_calendar.revoke import revoke_oauth_token
from pipeline.google_calendar.sync_status import get_job, get_latest_job
from pipeline.google_calendar.audit_log import log_action, get_history

router = APIRouter(prefix="/calendar", tags=["calendar"])

GOOGLE_AUTH_URL   = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL  = "https://oauth2.googleapis.com/token"
# Default matches nginx: FastAPI is mounted under /backend/ in production.
_DEFAULT_REDIRECT_URI = "https://aura.dau.ac.in/backend/calendar/callback"
CALENDAR_SCOPE_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
CALENDAR_SCOPE_EVENTS   = "https://www.googleapis.com/auth/calendar.events"


def _google_client_id() -> str:
    # Lazy — same Bug-8 pattern as token_vault: env may be loaded after import.
    return os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "").strip()


def _google_client_secret() -> str:
    return os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "").strip()


def _google_redirect_uri() -> str:
    """OAuth redirect URI for the FastAPI /calendar/callback route.

    Production (nginx): https://aura.dau.ac.in/backend/calendar/callback
    Local dev:          http://localhost:8000/calendar/callback

    A common misconfig is https://aura.dau.ac.in/calendar/callback (missing
    /backend/) — Google then redirects to the Next.js front door, which has
    no callback handler, and token exchange fails as an auth error.
    """
    uri = os.environ.get("GOOGLE_CALENDAR_REDIRECT_URI", _DEFAULT_REDIRECT_URI).strip()
    if (
        uri.endswith("/calendar/callback")
        and "/backend/calendar/callback" not in uri
        and "localhost" not in uri
        and "127.0.0.1" not in uri
    ):
        logger.warning(
            "GOOGLE_CALENDAR_REDIRECT_URI=%r is missing the /backend/ proxy "
            "prefix; OAuth callbacks will 404 on the frontend. Expected "
            "something like %r (must also match the Google Cloud authorized "
            "redirect URI).",
            uri,
            _DEFAULT_REDIRECT_URI,
        )
    return uri or _DEFAULT_REDIRECT_URI


def _frontend_origin() -> str:
    return os.environ.get("PROD_FRONTEND_ORIGIN", "http://localhost:3000").rstrip("/")


# ── Pydantic request/response models ────────────────────────────────────────

class SyncRequest(BaseModel):
    scope:        str = Field(default="full", pattern="^(full|today|this_week|subject)$")
    subject_code: str | None = None

class PreferenceUpdate(BaseModel):
    calendar_id:      str | None = None
    timezone:         str | None = None
    sync_policy:      str | None = Field(
        default=None,
        pattern="^(overwrite|merge|skip)$",
    )
    reminder_minutes: str | None = None   # e.g. "30,10,5"
    exam_calendar_id: str | None = None


# ── Faculty slot lookup ──────────────────────────────────────────────────────

@router.get("/slots/{faculty_erp_id}")
def get_faculty_slots(
    faculty_erp_id: str = Path(..., min_length=1, max_length=64),
    date: str = Query(..., min_length=10, max_length=10, description="Date in YYYY-MM-DD format"),
    identity: Identity = Depends(require_identity),
):
    try:
        target_date = datetime.date.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD format")

    if identity.role == "student":
        from erp_connector import ERPConnector
        erp = ERPConnector()
        shared    = erp.get_shared_courses(faculty_erp_id, identity.erp_id)
        btp       = erp.get_btp_students(faculty_erp_id)
        btp_rolls = [b["student_roll"] for b in btp]
        if not shared and identity.erp_id not in btp_rolls:
            raise HTTPException(
                status_code=403,
                detail="You can only view slots for faculty in your enrolled courses or your BTP guide.",
            )

    return get_available_slots(faculty_erp_id, target_date)


# ── OAuth connect / callback / disconnect / status ──────────────────────────

# SEC-05 fix: return_to used to be accepted as any string, lstrip("/")'d,
# and echoed back into a redirect after the OAuth callback. lstrip("/")
# blocks an absolute "//evil.com"-style open redirect, but path traversal
# ("../") or query-string injection ("?token=...") were never rejected, and
# the value was never checked against what the frontend actually has routes
# for before being signed into the JWT. Only known-safe paths are allowed now.
ALLOWED_RETURN_TO_PATHS = {"/", "/dashboard", "/settings/calendar"}


def _validate_return_to(value: str) -> str:
    if value in ALLOWED_RETURN_TO_PATHS:
        return value
    return "/dashboard"


def _post_oauth_redirect(return_to: str) -> str:
    """Build the browser redirect after a successful Google Calendar link."""
    path = _validate_return_to(return_to)
    origin = _frontend_origin()
    # Keep "/" as origin/?… — do not lstrip("/") (home would become an empty
    # path segment and depend on string formatting quirks).
    if path == "/":
        return f"{origin}/?calendar=connected"
    return f"{origin}{path}?calendar=connected"


@router.get("/connect")
def start_calendar_oauth(
    identity: Identity = Depends(require_identity),
    return_to: str = Query(default="/dashboard"),
):
    """Start Google Calendar OAuth flow. Returns JSON {"url": "..."} for frontend redirect."""
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Only students and faculty can connect a Google Calendar.")
    client_id = _google_client_id()
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CALENDAR_CLIENT_ID not configured.")
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")

    state_payload = {
        "erp_id":    identity.erp_id,
        "role":      identity.role,
        "return_to": _validate_return_to(return_to),
        "typ":       GCAL_OAUTH_STATE_TYP,
        "iss":       GCAL_OAUTH_STATE_ISSUER,
        "aud":       GCAL_OAUTH_STATE_AUDIENCE,
        "exp":       datetime.datetime.utcnow() + datetime.timedelta(minutes=10),
    }
    state_token = jwt.encode(state_payload, secret, algorithm=ALGORITHM)
    scope = CALENDAR_SCOPE_EVENTS if identity.role == "student" else CALENDAR_SCOPE_READONLY
    params = {
        "client_id":     client_id,
        "redirect_uri":  _google_redirect_uri(),
        "response_type": "code",
        "scope":         scope,
        "access_type":   "offline",
        "prompt":        "consent",
        "state":         state_token,
    }
    return {"url": GOOGLE_AUTH_URL + "?" + urllib.parse.urlencode(params)}


@router.get("/callback")
def calendar_oauth_callback(
    code:  str = Query(..., min_length=1, max_length=2048),
    state: str = Query(..., min_length=1, max_length=4096),
):
    import requests as _req
    secret = get_internal_jwt_secret()
    if not secret:
        raise HTTPException(status_code=500, detail="INTERNAL_JWT_SECRET not configured.")
    client_id = _google_client_id()
    client_secret = _google_client_secret()
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured.")

    try:
        claims = jwt.decode(state, secret, algorithms=[ALGORITHM],
                            audience=GCAL_OAUTH_STATE_AUDIENCE,
                            issuer=GCAL_OAUTH_STATE_ISSUER)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="State token expired. Please reconnect.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid state token. Possible CSRF attempt.")

    if claims.get("typ") != GCAL_OAUTH_STATE_TYP:
        raise HTTPException(status_code=400, detail="Invalid state token type.")

    erp_id = claims.get("erp_id")
    if not erp_id:
        raise HTTPException(status_code=400, detail="State token missing erp_id.")

    redirect_uri = _google_redirect_uri()
    resp = _req.post(GOOGLE_TOKEN_URL, data={
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  redirect_uri,
        "grant_type":    "authorization_code",
    }, timeout=10)
    if not resp.ok:
        logger.warning("Google Calendar token exchange failed (status %s): %s", resp.status_code, resp.text)
        raise HTTPException(status_code=400, detail="Google Calendar authorisation failed. Please try again.")

    data          = resp.json()
    access_token  = data.get("access_token")
    refresh_token = data.get("refresh_token")
    expires_in    = data.get("expires_in", 3600)
    expiry        = (datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)).isoformat()

    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="No refresh token returned. Ensure prompt=consent and access_type=offline.",
        )

    role  = claims.get("role", "faculty")
    scope = SCOPE_EVENTS if role == "student" else SCOPE_READONLY
    try:
        store_tokens(erp_id=erp_id, access_token=access_token,
                     refresh_token=refresh_token, token_expiry=expiry, scope=scope)
    except RuntimeError as exc:
        # Most often: GOOGLE_CALENDAR_VAULT_KEY unset — surface as config error,
        # not an opaque 500 after the user already completed Google consent.
        logger.error("Failed to persist Google Calendar tokens for %s: %s", erp_id, exc)
        raise HTTPException(
            status_code=500,
            detail="Google Calendar token storage is not configured. Set GOOGLE_CALENDAR_VAULT_KEY.",
        ) from exc

    # Auto-detect timezone from Google Calendar primary calendar
    try:
        import requests as _req2
        cal_resp = _req2.get(
            "https://www.googleapis.com/calendar/v3/calendars/primary",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if cal_resp.ok:
            tz = cal_resp.json().get("timeZone")
            if tz:
                update_preferences(erp_id, timezone=tz)
    except Exception:
        pass  # Non-critical — fall back to Asia/Kolkata default

    log_action(erp_id, "connect", "success", {"role": role, "scope": scope})

    return RedirectResponse(url=_post_oauth_redirect(claims.get("return_to", "/dashboard")))


@router.delete("/disconnect")
def disconnect_calendar(identity: Identity = Depends(require_identity)):
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Only students and faculty can disconnect a calendar.")

    erp_id = identity.erp_id

    if identity.role == "student":
        # 1. Remove all AURA-created events BEFORE dropping the token
        unsync_all(erp_id)

    # 2. Revoke Google OAuth token (best-effort — never blocks disconnect)
    revoke_oauth_token(erp_id)

    # 3. Drop local token + synced events
    unlink_calendar(erp_id)

    log_action(erp_id, "disconnect", "success", {"role": identity.role})
    return {"status": "disconnected"}


@router.get("/status")
def calendar_status(identity: Identity = Depends(require_identity)):
    if identity.role not in ("student", "faculty"):
        raise HTTPException(status_code=403, detail="Calendar status only available for students and faculty.")
    linked  = is_linked(identity.erp_id)
    payload = {"linked": linked, "erp_id": identity.erp_id}
    if identity.role == "student":
        payload["can_sync_timetable"] = linked and has_write_scope(identity.erp_id)
    return payload


# ── Timetable sync ──────────────────────────────────────────────────────────

@router.get("/timetable/sync/status")
def get_sync_status(
    identity: Identity = Depends(require_identity),
    job_id: str | None = Query(default=None),
):
    """
    Poll sync job status. With job_id returns that specific job;
    without job_id returns the most recent job for this student.
    """
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can check sync status.")
    job = get_job(job_id) if job_id else get_latest_job(identity.erp_id)
    if not job:
        return {"status": "no_sync_found"}
    if job["erp_id"] != identity.erp_id:
        raise HTTPException(status_code=403, detail="Not your sync job.")
    return job


@router.post("/timetable/sync/preview")
def preview_timetable_sync(
    body: SyncRequest,
    identity: Identity = Depends(require_identity),
):
    """Preview which events would be created/updated/deleted without writing anything."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can preview timetable sync.")
    result = timetable_sync.preview(identity, scope=body.scope, subject_code=body.subject_code)
    if result["status"] in ("calendar_not_connected", "error"):
        raise HTTPException(status_code=409, detail=result.get("message"))
    log_action(identity.erp_id, "preview", "success", {"scope": body.scope})
    return result


@router.post("/timetable/sync", status_code=202)
def sync_timetable_to_calendar(
    body: SyncRequest = SyncRequest(),
    identity: Identity = Depends(require_identity),
):
    """
    Enqueue a timetable → Google Calendar sync.
    Returns 202 Accepted + {"job_id": "..."} immediately.
    Poll GET /calendar/timetable/sync/status for completion.
    """
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can sync a timetable.")
    result = timetable_sync.apply(
        identity,
        scope=body.scope,
        subject_code=body.subject_code,
        async_mode=True,
    )
    if result["status"] == "calendar_not_connected":
        raise HTTPException(status_code=409, detail=result.get("message", "Google Calendar not connected."))
    if result["status"] == "already_running":
        raise HTTPException(status_code=409, detail=result.get("message", "Sync already in progress."))
    if result["status"] == "error":
        raise HTTPException(status_code=409, detail=result.get("message", "Could not sync timetable."))
    return result


@router.delete("/timetable/sync")
def unsync_timetable_from_calendar(
    identity: Identity = Depends(require_identity),
    keep_events: bool = Query(
        default=False,
        description="If true, keep existing Google Calendar events but stop managing them from AURA.",
    ),
):
    """Remove AURA-managed events from Google Calendar. Optionally keep them with keep_events=true."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can unsync a timetable.")
    result = timetable_sync.unsync(identity, keep_events=keep_events)
    log_action(identity.erp_id, "unsync", "success", result)
    return result


# ── Preferences ─────────────────────────────────────────────────────────────

@router.get("/preferences")
def get_calendar_preferences(identity: Identity = Depends(require_identity)):
    """Return the student's stored calendar preferences."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Preferences are only available for students.")
    try:
        prefs = get_preferences(identity.erp_id)
    except CalendarNotLinked:
        raise HTTPException(status_code=409, detail="No Google Calendar linked.")
    return prefs


@router.patch("/preferences")
def update_calendar_preferences(
    body: PreferenceUpdate,
    identity: Identity = Depends(require_identity),
):
    """Update one or more calendar preferences."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Preferences are only available for students.")
    if not is_linked(identity.erp_id):
        raise HTTPException(status_code=409, detail="No Google Calendar linked.")

    kwargs = {k: v for k, v in body.model_dump().items() if v is not None}
    update_preferences(identity.erp_id, **kwargs)
    log_action(identity.erp_id, "preferences_update", "success", kwargs)
    return {"status": "updated", "preferences": get_preferences(identity.erp_id)}


# ── Google Calendar list ─────────────────────────────────────────────────────

@router.get("/calendars")
def list_google_calendars(identity: Identity = Depends(require_identity)):
    """
    Fetch the student's list of Google Calendars so they can choose which
    one to sync into (multi-calendar support, Issue #13).
    """
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can list calendars.")
    if not is_linked(identity.erp_id) or not has_write_scope(identity.erp_id):
        raise HTTPException(status_code=409, detail="Google Calendar not connected with write scope.")

    import requests as _req
    from pipeline.google_calendar.client import get_valid_access_token
    try:
        token = get_valid_access_token(identity.erp_id)
        resp  = _req.get(
            "https://www.googleapis.com/calendar/v3/users/me/calendarList",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        return {
            "calendars": [
                {
                    "id":      c.get("id"),
                    "summary": c.get("summary"),
                    "primary": c.get("primary", False),
                }
                for c in items
            ]
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not fetch calendar list: {exc}")


# ── Audit log ────────────────────────────────────────────────────────────────

@router.get("/audit")
def get_calendar_audit_log(
    identity: Identity = Depends(require_identity),
    limit: int = Query(default=50, ge=1, le=200),
):
    """Return the student's calendar sync audit history (newest first)."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Audit log is only available for students.")
    return {"history": get_history(identity.erp_id, limit=limit)}
