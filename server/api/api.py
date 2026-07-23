import os
import sys
import tempfile
import asyncio
import threading
from typing import List, Optional
from pathlib import Path

server_dir = Path(__file__).resolve().parent.parent
rag_dir    = server_dir / "rag"
for p in (str(server_dir), str(rag_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(server_dir / ".env")
load_dotenv(rag_dir / ".env")

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from pipeline.speech import transcribe_audio
from api.auth import require_identity, Identity
from api.routes.identity_routes import router as identity_router
from api.routes.admin_routes import router as admin_router
from api.routes.calendar_routes import router as calendar_router
from pipeline.ecampus.credentials_vault import (
    store_credentials, unlink_credentials, is_linked
)
from pipeline.timetable import service as timetable_service
from pipeline.timetable.notifier import start_scheduler, stop_scheduler

app = FastAPI(title="AURA API")

# Lazy-init: AURA pulls in Pinecone, embeddings, etc. Defer until first /chat
# so /health and auth routes stay available during cold start.
_aura = None
_aura_lock = threading.Lock()


def get_aura():
    global _aura
    if _aura is None:
        with _aura_lock:
            if _aura is None:
                from rag import AURA  # noqa: PLC0415 — deferred heavy import
                _aura = AURA()
    return _aura

# ── CORS ──────────────────────────────────────────────────────────────────
# allow_credentials=True is REQUIRED for httpOnly cookies to be forwarded
# cross-origin (Next.js :3000 → FastAPI :8000 in dev). Must pair with
# explicit allow_origins — "*" is rejected by browsers when credentials=True.
ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
prod = os.getenv("PROD_FRONTEND_ORIGIN")
if prod:
    ALLOWED_ORIGINS.append(prod)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────
# identity_router: /internal/resolve-identity (called by Next.js at login)
# admin_router:    /admin/* (role_bindings management)
# No auth_router — login/refresh/logout are handled entirely by NextAuth.js
app.include_router(identity_router)
app.include_router(admin_router)
app.include_router(calendar_router)


@app.on_event("startup")
async def _startup():
    """Start the timetable push-notification scheduler."""
    try:
        await start_scheduler()
    except Exception:
        import logging
        logging.getLogger("aura.api").warning("Notification scheduler failed to start (non-fatal).")


@app.on_event("shutdown")
async def _shutdown():
    """Stop the timetable push-notification scheduler."""
    await stop_scheduler()

# ── Whisper concurrency lock ──────────────────────────────────────────────
speech_queue_lock = asyncio.Semaphore(1)

ffmpeg_path = os.getenv("FFMPEG_BINARY_PATH")
if ffmpeg_path and os.path.exists(ffmpeg_path):
    if ffmpeg_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + ffmpeg_path

UNIVERSITY_PROMPT = (
    "Dhirubhai Ambani University, DAU, DA-IICT, Gandhinagar. "
    "B.Tech ICT, B.Tech CS AI, B.Tech ECE, BS-MS, M.Tech, M.Sc, M.Des, Ph.D. "
    "AURA, CGPA, semester, admissions, fees, hostel, scholarship, placement."
)

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
    question:    str
    history:     Optional[List[HistoryTurn]] = None
    userProfile: Optional[UserProfile]       = None

class LinkEcampusRequest(BaseModel):
    ecampus_username: str
    ecampus_password: str

ALLOWED_AUDIO   = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024

# ── /chat ─────────────────────────────────────────────────────────────────
@app.post("/chat")
def chat(
    request:  ChatRequest,
    identity: Identity = Depends(require_identity),   # verifies Next.js JWT
):
    history = [t.model_dump() for t in request.history] if request.history else []
    display_profile = (
        request.userProfile.model_dump(exclude_none=True)
        if request.userProfile else None
    )
    return get_aura().ask(
        question=request.question,
        history=history,
        identity=identity.as_dict(),
        display_profile=display_profile,
    )

# ── eCampus account linking ───────────────────────────────────────────────
# These three endpoints handle optional eCampus credential storage for the
# scraper path. They are NOT auth endpoints — they manage the vault that
# lets AURA log into ecampus.daiict.ac.in on a student's behalf to scrape
# personal data (when direct ERP DB access is unavailable).
@app.post("/ecampus/link")
def link_ecampus(
    request:  LinkEcampusRequest,
    identity: Identity = Depends(require_identity),
):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can link an eCampus account.")
    store_credentials(identity.erp_id, request.ecampus_username, request.ecampus_password)
    return {"status": "linked"}

@app.delete("/ecampus/link")
def unlink_ecampus(identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can unlink.")
    unlink_credentials(identity.erp_id)
    return {"status": "unlinked"}

@app.get("/ecampus/link")
def ecampus_link_status(identity: Identity = Depends(require_identity)):
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students have a link status.")
    return {"linked": is_linked(identity.erp_id)}

# ── /speech ───────────────────────────────────────────────────────────────
@app.post("/speech")
async def speech(
    file:     UploadFile = File(...),
    identity: Identity   = Depends(require_identity),
):
    temp_path = None
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_AUDIO:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_AUDIO_BYTES:
                    raise HTTPException(status_code=413, detail="Audio file too large")
                tmp.write(chunk)
            temp_path = tmp.name

        async with speech_queue_lock:
            question = await run_in_threadpool(
                transcribe_audio, temp_path, initial_prompt=UNIVERSITY_PROMPT
            )
        return {"text": question}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health")
async def health():
    # Public: only confirms the server is alive. No secrets, no env detail.
    return {"status": "online", "service": "AURA API"}

@app.get("/health/detail")
async def health_detail(identity: Identity = Depends(require_identity)):
    # Authenticated admins only
    if identity.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden")
    return {
        "INTERNAL_JWT_SECRET":    bool(os.getenv("INTERNAL_JWT_SECRET")),
        "AUTH_DB_URL":            bool(os.getenv("AUTH_DB_URL")),
        "ERP_DB_HOST":            bool(os.getenv("ERP_DB_HOST")),
    }


# -- Timetable API routes -------------------------------------------------------


class PushSubscription(BaseModel):
    endpoint: str
    keys: dict


@app.get("/timetable/me")
def timetable_me(identity: Identity = Depends(require_identity)):
    """Student's effective timetable (master + personal overrides)."""
    try:
        return timetable_service.get_effective_timetable(identity)
    except timetable_service.TimetableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/timetable/faculty")
def timetable_faculty(identity: Identity = Depends(require_identity)):
    """Faculty member's full teaching schedule across all batches."""
    try:
        return timetable_service.get_faculty_timetable(identity)
    except timetable_service.TimetableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/timetable/changes")
def timetable_changes(identity: Identity = Depends(require_identity)):
    """List student's personal timetable overrides."""
    try:
        return {"changes": timetable_service.list_my_changes(identity)}
    except timetable_service.TimetableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/push/subscribe")
def push_subscribe(
    subscription: PushSubscription,
    identity: Identity = Depends(require_identity),
):
    """Register a Web Push subscription for class reminders."""
    import db.connection as db_conn
    db_conn.execute(
        """INSERT INTO push_subscriptions (erp_id, endpoint, p256dh, auth_key)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (endpoint) DO UPDATE SET
             p256dh = EXCLUDED.p256dh, auth_key = EXCLUDED.auth_key, last_seen_at = now()""",
        (
            identity.erp_id,
            subscription.endpoint,
            subscription.keys.get("p256dh", ""),
            subscription.keys.get("auth", ""),
        ),
    )
    return {"status": "subscribed"}


@app.get("/push/vapid-public-key")
def vapid_public_key():
    """Return the VAPID public key for Web Push subscription."""
    key = os.environ.get("VAPID_PUBLIC_KEY", "")
    if not key:
        raise HTTPException(status_code=503, detail="VAPID_PUBLIC_KEY is not configured.")
    return {"publicKey": key}


@app.delete("/push/subscribe")
def push_unsubscribe(
    endpoint: str,
    identity: Identity = Depends(require_identity),
):
    """Remove a Web Push subscription by endpoint URL."""
    import db.connection as db_conn
    db_conn.execute(
        """DELETE FROM push_subscriptions
           WHERE erp_id = %s AND endpoint = %s""",
        (identity.erp_id, endpoint),
    )
    return {"status": "unsubscribed"}


# -- Elective selection routes -------------------------------------------------


class ElectiveSelectionsRequest(BaseModel):
    course_codes: list[str]


@app.get("/timetable/electives")
def timetable_electives(identity: Identity = Depends(require_identity)):
    """Available elective courses for the student's cohort, with selection status."""
    try:
        return timetable_service.get_available_electives(identity)
    except timetable_service.TimetableError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/timetable/electives")
def save_elective_selections(
    request: ElectiveSelectionsRequest,
    identity: Identity = Depends(require_identity),
):
    """Save the student's elective course selections."""
    try:
        return timetable_service.save_elective_selections(identity, request.course_codes)
    except timetable_service.TimetableError as e:
        raise HTTPException(status_code=400, detail=str(e))


# -- Student profile / cohort onboarding routes -------------------------------


class CohortUpdateRequest(BaseModel):
    program: str        # "BTech", "BS-MS", "MSc", "MTech"
    year: int           # 1, 2, 3, 4
    semester: int       # 1-10
    section: str        # "A", "B", "C", "D"
    branch: Optional[str] = None  # "IT", "DS + AI", "AA", etc.


@app.get("/profile/cohort")
def get_cohort(identity: Identity = Depends(require_identity)):
    """Returns the student's current cohort fields (or null if not set)."""
    return {
        "erp_id": identity.erp_id,
        "current_year": identity.current_year,
        "current_sem": identity.current_sem,
        "current_sec": identity.current_sec,
        "is_configured": (
            identity.current_year is not None
            and identity.current_sem is not None
            and identity.current_sec is not None
        ),
    }


@app.get("/profile/cohort-options")
def get_cohort_options(identity: Identity = Depends(require_identity)):
    """Returns available programs, years, and sections from timetable_master.
    Used by the onboarding UI to populate dropdowns dynamically."""
    import db.connection as db_conn

    rows = db_conn.query(
        """SELECT DISTINCT program, year, sem, sec, branch
           FROM timetable_master
           WHERE program IS NOT NULL
             AND program != 'Elective'
             AND year > 0
           ORDER BY program, year, sem, sec""",
        (),
    )

    # Build structured options
    programs: dict[str, dict] = {}
    for row in rows:
        prog = row["program"]
        if prog not in programs:
            programs[prog] = {"years": {}, "branches": set()}
        yr = row["year"]
        sem = row["sem"]
        sec = row.get("sec")
        branch = row.get("branch", "")
        if branch:
            programs[prog]["branches"].add(branch)
        if yr not in programs[prog]["years"]:
            programs[prog]["years"][yr] = {"semesters": set(), "sections": set()}
        programs[prog]["years"][yr]["semesters"].add(sem)
        if sec:
            programs[prog]["years"][yr]["sections"].add(sec)

    # Convert sets to sorted lists for JSON serialization
    result = []
    for prog, data in sorted(programs.items()):
        years = []
        for yr, yr_data in sorted(data["years"].items()):
            years.append({
                "year": yr,
                "semesters": sorted(yr_data["semesters"]),
                "sections": sorted(yr_data["sections"]),
            })
        result.append({
            "program": prog,
            "branches": sorted(data["branches"]),
            "years": years,
        })

    return {"options": result}


@app.post("/profile/cohort")
def save_cohort(
    request: CohortUpdateRequest,
    identity: Identity = Depends(require_identity),
):
    """Save the student's program/year/semester/section to user_identity_map.
    Only students can set their own cohort. Validates that the combination
    exists in timetable_master before saving."""
    if identity.role != "student":
        raise HTTPException(status_code=403, detail="Only students can set a cohort profile.")

    import db.connection as db_conn

    # Validate the cohort exists in timetable_master
    check = db_conn.query(
        """SELECT 1 FROM timetable_master
           WHERE year = %s AND sem = %s AND sec = %s
           LIMIT 1""",
        (request.year, request.semester, request.section),
    )
    if not check:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No timetable data found for Year {request.year}, "
                f"Semester {request.semester}, Section {request.section}. "
                "Please check your selection."
            ),
        )

    # Update user_identity_map
    db_conn.execute(
        """UPDATE user_identity_map
           SET current_year = %s, current_sem = %s, current_sec = %s
           WHERE erp_id = %s""",
        (request.year, request.semester, request.section, identity.erp_id),
    )

    return {
        "status": "saved",
        "current_year": request.year,
        "current_sem": request.semester,
        "current_sec": request.section,
    }