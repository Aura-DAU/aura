import json
import os
import time
from pathlib import Path
import numpy as np
import requests
from dotenv import load_dotenv

load_dotenv()

# Setup paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
CHUNKS_FILE = SCRIPT_DIR / "../../../processed_chunks/chunks.json"
VECTOR_STORE_DIR = SCRIPT_DIR / "../../vector_store"
EMBEDDINGS_FILE = VECTOR_STORE_DIR / "embeddings.npy"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.json"

# Node 4 embedding-reranker service (not legacy TEI on :8081)
EMBEDDING_URL = os.getenv("EMBEDDING_URL") or os.getenv(
    "EMBEDDING_SERVICE_URL", "http://10.100.97.74:8001"
)
BATCH_SIZE = 32
MAX_RETRIES = 8
RETRY_BASE_SECONDS = 2


def load_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_service_ready(embedding_url: str) -> None:
    health_url = f"{embedding_url.rstrip('/')}/health"
    try:
        resp = requests.get(health_url, timeout=10)
        resp.raise_for_status()
        health = resp.json()
    except Exception as exc:
        raise RuntimeError(
            f"Embedding service unreachable at {health_url}. "
            f"On Node 4 check: docker compose ps && docker compose logs embedding-reranker. ({exc})"
        ) from exc

    if not health.get("embedding_loaded"):
        raise RuntimeError(
            f"Embedding model not loaded on {health_url}: {health}. "
            "Restart embedding-reranker on Node 4 and wait until /health shows embedding_loaded=true."
        )
    print(f"Embedding service healthy: model={health.get('embedding_model')} device={health.get('device')}")


def post_embed(endpoint: str, batch_texts: list[str]) -> list:
    payload = {"texts": batch_texts, "normalize": True}
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=300,
        )
        if response.status_code == 200:
            data = response.json()
            return data["embeddings"] if isinstance(data, dict) else data

        detail = response.text[:500]
        # 503 = model not ready or inference semaphore busy — retry with backoff
        if response.status_code == 503 and attempt < MAX_RETRIES:
            wait = RETRY_BASE_SECONDS * (2 ** (attempt - 1))
            print(f"  503 from embed service ({detail}); retry {attempt}/{MAX_RETRIES} in {wait}s...")
            time.sleep(wait)
            last_error = requests.HTTPError(
                f"503 Server Error: {detail}", response=response
            )
            continue

        raise requests.HTTPError(
            f"{response.status_code} Error for {endpoint}: {detail}",
            response=response,
        )

    assert last_error is not None
    raise last_error


def generate_embeddings(texts, embedding_url, batch_size=32):
    ensure_service_ready(embedding_url)
    endpoint = f"{embedding_url.rstrip('/')}/embed"
    all_embeddings = []
    total = len(texts)
    print(f"Requesting embeddings from {endpoint} for {total} texts in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch_texts = texts[i:i + batch_size]
        batch_vecs = post_embed(endpoint, batch_texts)
        all_embeddings.extend(batch_vecs)
        if (i + batch_size) % 320 == 0 or (i + batch_size) >= total:
            print(f"  Processed {min(i + batch_size, total)}/{total} chunks")

    embeddings = np.array(all_embeddings, dtype="float32")

    # L2 Normalization check/enforcement
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = (embeddings / np.maximum(norms, 1e-12)).astype("float32")

    return embeddings


def main():
    print("Loading chunks...")
    chunks = load_chunks(CHUNKS_FILE)
    print(f"Loaded {len(chunks)} chunks")

    texts = [chunk["text"] for chunk in chunks]

    print("Generating embeddings via embedding-reranker service...")
    embeddings = generate_embeddings(texts, EMBEDDING_URL, BATCH_SIZE)

    print(f"\nEmbedding shape: {embeddings.shape}")

    # SAVE OUTPUTS
    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

    np.save(EMBEDDINGS_FILE, embeddings)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    print("\nSaved embeddings")
    print(f"Embeddings -> {EMBEDDINGS_FILE}")
    print(f"Metadata -> {METADATA_FILE}")


if __name__ == "__main__":
    main()
