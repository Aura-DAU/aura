import json
import os
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


def load_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_embeddings(texts, embedding_url, batch_size=32):
    endpoint = f"{embedding_url.rstrip('/')}/embed"
    all_embeddings = []
    total = len(texts)
    print(f"Requesting embeddings from {endpoint} for {total} texts in batches of {batch_size}...")

    for i in range(0, total, batch_size):
        batch_texts = texts[i:i + batch_size]
        # Matches services/embedding-reranker EmbedRequest
        payload = {"texts": batch_texts, "normalize": True}
        response = requests.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        batch_vecs = data["embeddings"] if isinstance(data, dict) else data
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
