FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# Run as an unprivileged user. HF_HOME points at a dir the user owns so model
# weights can be cached at runtime (no HF cache volume is mounted for this service).
ENV HF_HOME=/home/appuser/.cache/huggingface
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p "$HF_HOME" \
    && chown -R appuser:appuser /app "$HF_HOME"
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=15s --timeout=5s --retries=5 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--limit-concurrency", "16", "--timeout-keep-alive", "5"]
