# ── AURA Embedding Service ────────────────────────────────────────────────
# Architecture PDF Section 9: "Embedding Generation Service" (aura-embedding)
# Deployed on Node 4 (RTX 5080) alongside the reranker.
#
# GPU build: uses pytorch/pytorch base which includes CUDA.
# CPU-only build: replace base image with python:3.11-slim and remove nvidia
#                 runtime references.
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model at build time so container starts instantly.
# Change EMBEDDING_MODEL build-arg to use a different model.
ARG EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('${EMBEDDING_MODEL}')"

COPY main.py .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
