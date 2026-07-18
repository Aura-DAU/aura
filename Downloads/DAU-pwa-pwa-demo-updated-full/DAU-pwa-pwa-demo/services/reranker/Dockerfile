# ── AURA Cross-Encoder Reranker Service ──────────────────────────────────
# Architecture PDF Section 11: "Cross-Encoder Re-ranking Service" (aura-reranker)
# Deployed on Node 4 (RTX 5080) alongside the embedding service.
FROM pytorch/pytorch:2.3.1-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download model at build time for faster container startup.
ARG RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
    AutoTokenizer.from_pretrained('${RERANKER_MODEL}'); \
    AutoModelForSequenceClassification.from_pretrained('${RERANKER_MODEL}')"

COPY main.py .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
