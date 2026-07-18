"""
AURA FastAPI application entry point.

Responsibilities:
  - Wire up all routers (identity, admin, calendar, timetable, chat, speech, health)
  - Configure CORS
  - Attach latency-logging middleware
  - Manage application lifespan (timetable scheduler start/stop)
  - Serve /documents (citation source files)
  - Expose the get_aura() singleton for chat_routes.py
"""
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

server_dir = Path(__file__).resolve().parent.parent
rag_dir    = server_dir / "rag"
for p in (str(server_dir), str(rag_dir)):
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.auth import require_identity, Identity
from api.routes.identity_routes  import router as identity_router
from api.routes.admin_routes      import router as admin_router
from api.routes.calendar_routes   import router as calendar_router
from api.routes.timetable_routes  import router as timetable_router, push_router
from api.routes.chat_routes       import router as chat_router
from api.routes.speech_routes     import router as speech_router
from api.routes.health_routes     import router as health_router
from pipeline.latency_tracker import init_tracker, reset_tracker
from db.connection import execute


# ── Application lifespan (replaces deprecated @app.on_event) ─────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background jobs on startup; stop them cleanly on shutdown."""
    from pipeline.timetable.notifier import start_scheduler, stop_scheduler  # noqa: PLC0415
    start_scheduler()
    yield
    stop_scheduler()


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="AURA API", lifespan=lifespan)


# ── CORS ──────────────────────────────────────────────────────────────────
# allow_credentials=True is REQUIRED for httpOnly cookies to be forwarded
# cross-origin (Next.js :3000 → FastAPI :8000 in dev). Must pair with
# explicit allow_origins — "*" is rejected by browsers when credentials=True.
ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
prod = os.getenv("PROD_FRONTEND_ORIGIN")
if prod:
    ALLOWED_ORIGINS.append(prod)


# ── Latency Logging Middleware ────────────────────────────────────────────
@app.middleware("http")
async def log_latency_middleware(request, call_next):
    if request.url.path != "/chat":
        return await call_next(request)

    data, token = init_tracker()
    t0 = time.time()
    try:
        response = await call_next(request)
        total_time = time.time() - t0

        # Log asynchronously so we do not block the client's HTTP response.
        from fastapi.background import BackgroundTasks  # noqa: PLC0415

        def _write_log():
            try:
                execute(
                    "INSERT INTO latency_logs (guardrail_time, retrieval_time, generation_time, total_time) "
                    "VALUES (%s, %s, %s, %s)",
                    (
                        data.get("guardrail_time",  0.0),
                        data.get("retrieval_time",  0.0),
                        data.get("generation_time", 0.0),
                        total_time,
                    ),
                )
            except Exception as e:
                print(f"[latency_middleware] Failed to log latency: {e}")

        bg_tasks = BackgroundTasks()
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


# ── Routers ───────────────────────────────────────────────────────────────
# identity_router:  /internal/resolve-identity  (called by Next.js at login)
# admin_router:     /admin/*                    (role_bindings management)
# calendar_router:  /calendar/*
# timetable_router: /timetable/*
# push_router:      /push/*
# chat_router:      /chat
# speech_router:    /speech
# health_router:    /health, /health/detail
app.include_router(identity_router)
app.include_router(admin_router)
app.include_router(calendar_router)
app.include_router(timetable_router)
app.include_router(push_router)
app.include_router(chat_router)
app.include_router(speech_router)
app.include_router(health_router)


# ── /documents ────────────────────────────────────────────────────────────
# Serves the raw markdown source behind a citation card so the frontend
# side-drawer can render it. `doc_path` is the "path" field the frontend
# receives on each citation — ContextBuilder's `relative_path`
# (e.g. "infrastructure/ict_infrastructure.md"). Never a filesystem path
# supplied by the client; resolved strictly under DATA_ROOT.
DATA_ROOT = (server_dir.parent / "data").resolve()


@app.get("/documents/{doc_path:path}")
async def get_document(
    doc_path: str,
    identity: Identity = Depends(require_identity),
):
    # Citations may carry either "data/foo/bar.md" or "foo/bar.md" — strip
    # a leading "data/" prefix before resolving so both forms work.
    normalised = doc_path[len("data/"):] if doc_path.startswith("data/") else doc_path
    candidate  = (DATA_ROOT / normalised).resolve()

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
        "path":        normalised,
        "content":     content,
        "total_lines": content.count("\n") + 1,
    }