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

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from api.auth import require_identity, Identity
from api.routes.identity_routes import router as identity_router
from api.routes.admin_routes import router as admin_router
from api.routes.calendar_routes import router as calendar_router
from api.routes.timetable_routes import router as timetable_router, push_router
from pipeline.ecampus.credentials_vault import (
    store_credentials, unlink_credentials, is_linked
)
from pipeline.rate_limiter import enforce_quota, QuotaExceeded

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


# ── Latency Logging Middleware ───────────────────────────────────────────
from pipeline.latency_tracker import init_tracker, reset_tracker
from db.connection import execute
import time
from fastapi import Response
from api.metrics import REQUEST_COUNT, REQUEST_LATENCY, STAGE_LATENCY, metrics_response

# ── Prometheus scrape endpoint (architecture doc: aura-prometheus) ────────
# Never routed through the public NGINX edge — see deploy/nginx.conf, which
# only proxies /api/*, /backend/, and /. Prometheus scrapes this container
# directly over the internal Docker network.
@app.get("/metrics")
async def metrics():
    body, content_type = metrics_response()
    return Response(content=body, media_type=content_type)


@app.middleware("http")
async def prometheus_request_middleware(request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)
    t0 = time.time()
    response = await call_next(request)
    duration = time.time() - t0
    # request.url.path is used directly (not templated) since AURA's route
    # set is small and fixed; high-cardinality paths (e.g. /documents/{id})
    # would need templating first if added later.
    REQUEST_LATENCY.labels(method=request.method, path=request.url.path).observe(duration)
    REQUEST_COUNT.labels(method=request.method, path=request.url.path, status=response.status_code).inc()
    return response


@app.middleware("http")
async def log_latency_middleware(request, call_next):
    if request.url.path != "/chat":
        return await call_next(request)
        
    data, token = init_tracker()
    t0 = time.time()
    try:
        response = await call_next(request)
        total_time = time.time() - t0

        # Feed the same per-stage breakdown into Prometheus histograms so
        # Grafana can chart the doc's critical-path stages (§Understanding
        # the Critical Path) alongside the Postgres-backed latency_logs
        # table used for durable analytics/admin reporting.
        STAGE_LATENCY.labels(stage="guardrail").observe(data.get("guardrail_time", 0.0))
        STAGE_LATENCY.labels(stage="retrieval").observe(data.get("retrieval_time", 0.0))
        STAGE_LATENCY.labels(stage="generation").observe(data.get("generation_time", 0.0))
        STAGE_LATENCY.labels(stage="total").observe(total_time)

        # Log asynchronously in the background so we do not block the client's HTTP response
        from fastapi.background import BackgroundTasks
        bg_tasks = BackgroundTasks()
        
        def _write_log():
            try:
                execute(
                    "INSERT INTO latency_logs (guardrail_time, retrieval_time, generation_time, total_time) "
                    "VALUES (%s, %s, %s, %s)",
                    (
                        data.get("guardrail_time", 0.0),
                        data.get("retrieval_time", 0.0),
                        data.get("generation_time", 0.0),
                        total_time
                    )
                )
            except Exception as e:
                print(f"[latency_middleware] Failed to log latency: {e}")
                
        bg_tasks.add_task(_write_log)
        response.background = bg_tasks
        
        return response
    finally:
        reset_tracker(token)

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
app.include_router(timetable_router)
app.include_router(push_router)


@app.on_event("startup")
async def _start_timetable_scheduler():
    """Kicks off the '10 minutes before class' push-notification background
    job. See pipeline/timetable/notifier.py for the tick logic."""
    from pipeline.timetable.notifier import start_scheduler
    start_scheduler()


@app.on_event("shutdown")
async def _stop_timetable_scheduler():
    from pipeline.timetable.notifier import stop_scheduler
    stop_scheduler()

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
    question:       str
    history:        Optional[List[HistoryTurn]] = None
    userProfile:    Optional[UserProfile]       = None
    studentProfile: Optional[UserProfile]       = None

    def resolved_profile(self) -> Optional[UserProfile]:
        return self.studentProfile or self.userProfile

class LinkEcampusRequest(BaseModel):
    ecampus_username: str
    ecampus_password: str

ALLOWED_AUDIO   = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024

# ── /chat ─────────────────────────────────────────────────────────────────
@app.post("/chat")
async def chat(
    request:  ChatRequest,
    identity: Identity = Depends(require_identity),   # verifies Next.js JWT
):
    history = [t.model_dump() for t in (request.history or [])][-6:]
    profile = request.resolved_profile()
    display_profile = profile.model_dump(exclude_none=True) if profile else None

    quota_key = identity.email or identity.erp_id
    try:
        enforce_quota(quota_key, identity.role)
    except QuotaExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail=f"Question limit reached ({exc.limit}/day).",
        ) from exc

    return await run_in_threadpool(
        get_aura().ask,
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
            # Defer Whisper import/load until first /speech call so /health can boot.
            from pipeline.speech import transcribe_audio

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

# ── /documents ────────────────────────────────────────────────────────────
# Phase C (FE-3/BE-2): serves the raw markdown source behind a citation card
# so the frontend side-drawer can render it and scroll/highlight the exact
# lines a chunk was drawn from. `doc_path` is the "path" field the frontend
# receives on each citation — this is ContextBuilder's `relative_path`
# (e.g. "infrastructure/ict_infrastructure.md" or
# "data/infrastructure/ict_infrastructure.md"), never a filesystem path
# supplied by the client, so we resolve it strictly under DATA_ROOT below.
DATA_ROOT = (server_dir.parent / "data").resolve()

@app.get("/documents/{doc_path:path}")
async def get_document(
    doc_path: str,
    identity: Identity = Depends(require_identity),  # verifies Next.js JWT
):
    # Citations may carry either "data/foo/bar.md" or "foo/bar.md" — accept
    # both by stripping a leading "data/" segment before resolving.
    normalised = doc_path[len("data/"):] if doc_path.startswith("data/") else doc_path

    candidate = (DATA_ROOT / normalised).resolve()

    # Path-traversal guard: the resolved path must stay inside DATA_ROOT.
    if DATA_ROOT not in candidate.parents and candidate != DATA_ROOT:
        raise HTTPException(status_code=400, detail="Invalid document path")

    if candidate.suffix.lower() != ".md":
        raise HTTPException(status_code=400, detail="Only markdown sources can be viewed")

    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        content = candidate.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=500, detail="Could not read document") from exc

    return {
        "path": normalised,
        "content": content,
        "total_lines": content.count("\n") + 1,
    }

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