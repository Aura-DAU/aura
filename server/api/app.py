# FastAPI app factory — CORS, latency middleware, routers.
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

_server_dir = Path(__file__).resolve().parent.parent
_rag_dir = _server_dir / "rag"
for _p in (str(_server_dir), str(_rag_dir)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api.deps import warm_aura_in_background
from api.middleware.latency import register_latency_middleware
from api.routes.admin_routes import router as admin_router
from api.routes.calendar_routes import router as calendar_router
from api.routes.chat_routes import router as chat_router
from api.routes.ecampus_routes import router as ecampus_router
from api.routes.health_routes import router as health_router
from api.routes.identity_routes import router as identity_router
from api.routes.speech_routes import router as speech_router


@asynccontextmanager
async def _lifespan(application: FastAPI):
    # Pre-load the RAG stack in the background so the first real /chat does
    # not pay the multi-second model init. AURA_WARMUP=0 opts out (e.g. when
    # running the API only for non-chat routes).
    if os.getenv("AURA_WARMUP", "1") != "0":
        warm_aura_in_background()
    yield


def create_app() -> FastAPI:
    application = FastAPI(title="AURA API", lifespan=_lifespan)

    # Credentials require explicit origins (browsers reject "*" with credentials).
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
    prod = os.getenv("PROD_FRONTEND_ORIGIN")
    if prod:
        allowed_origins.append(prod)

    register_latency_middleware(application)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Login/refresh/logout stay in NextAuth — no auth_router here.
    application.include_router(identity_router)
    application.include_router(admin_router)
    application.include_router(calendar_router)
    application.include_router(chat_router)
    application.include_router(speech_router)
    application.include_router(ecampus_router)
    application.include_router(health_router)

    ffmpeg_path = os.getenv("FFMPEG_BINARY_PATH")
    if ffmpeg_path and os.path.exists(ffmpeg_path):
        if ffmpeg_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] += os.pathsep + ffmpeg_path

    return application


app = create_app()
