"""
FastAPI application entry point.

Startup lifecycle:
  1. Load all .md documents from DATA_DIR into memory.
  2. Build the sentence-transformer embedding index.
  3. Begin accepting requests.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.core.config import settings
from app.core.rag import build_index, load_corpus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AURA backend starting — loading corpus and building RAG index…")
    corpus = load_corpus()
    build_index(corpus)
    logger.info("RAG index ready. AURA backend is live.")
    yield
    logger.info("AURA backend shutting down.")


app = FastAPI(
    title="AURA RAG API",
    description=(
        "Retrieval-Augmented Generation backend for the AURA student assistant "
        "at Dhirubhai Ambani University."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "AURA RAG API"}
