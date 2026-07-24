# AURA backend (FastAPI + RAG pipeline) — Phase E (DO-4)
#
# Installs system dependencies (FFmpeg, required by openai-whisper for the
# /speech transcription endpoint) plus the Python requirements, then serves
# the app with Gunicorn managing Uvicorn workers.
#
# Build from the repo root:
#   docker build -f server/Dockerfile -t aura-backend ./server

FROM python:3.11-slim AS base

# ffmpeg          — audio decoding for pipeline.speech / openai-whisper
# libpq-dev/gcc   — build psycopg2 (AUTH_DB_URL) if a wheel isn't available
# curl            — container healthcheck against /health
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ffmpeg \
      libpq-dev \
      gcc \
      curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app/server

COPY rag/requirements.txt ./rag/requirements.txt
RUN pip install --no-cache-dir -r rag/requirements.txt \
 && pip install --no-cache-dir gunicorn

# api.py inserts server_dir and rag_dir onto sys.path itself, so the image
# just needs the whole server/ tree with this as the working directory.
COPY . .

# System users default HOME=/nonexistent; Whisper/HF caches need a real path.
RUN addgroup --system aura && adduser --system --ingroup aura aura \
 && mkdir -p /var/lib/aura/whisper /var/log/aura \
 && chown -R aura:aura /app/server /var/lib/aura /var/log/aura
USER aura

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    HOME=/tmp \
    XDG_CACHE_HOME=/tmp/.cache \
    WHISPER_CACHE_DIR=/tmp/whisper-cache

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS "http://localhost:${PORT}/health" || exit 1

# Default workers via WEB_CONCURRENCY — the RAG pipeline (Qdrant client,
# in-process embedder/reranker, LangGraph orchestrator) is lazily
# initialised per-process on first /chat call, so extra workers multiply
# cold-start memory. Override WEB_CONCURRENCY to scale out.
# Request-line/header caps blunt header-flood DoS; max-requests recycles
# workers to bound memory growth from long-lived RAG caches.
CMD ["sh", "-c", "gunicorn api.api:app -k uvicorn.workers.UvicornWorker --workers ${WEB_CONCURRENCY:-2} --bind 0.0.0.0:${PORT} --timeout 120 --limit-request-line 8190 --limit-request-fields 100 --limit-request-field_size 8190 --max-requests ${GUNICORN_MAX_REQUESTS:-1000} --max-requests-jitter 100"]
