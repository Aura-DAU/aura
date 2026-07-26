"""
upload_to_qdrant.py — Ingestion pipeline vector uploader to Qdrant.

Reads embeddings.npy and metadata.json, formats metadata payloads,
ensures the target collection exists (768-dim, COSINE distance), and
upserts vector points into Qdrant using parallel threads.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from tqdm import tqdm

load_dotenv()

# Setup paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
EMBEDDINGS_FILE = SCRIPT_DIR / "../../vector_store/embeddings.npy"
METADATA_FILE = SCRIPT_DIR / "../../vector_store/metadata.json"

QDRANT_URL = os.getenv("QDRANT_URL", "http://10.100.97.74:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY") or None
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "aura_documents")
BATCH_SIZE = 100


def chunk_list(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i : i + batch_size]


def main():
    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    print("Loading embeddings...")
    embeddings = np.load(EMBEDDINGS_FILE)

    print("Loading metadata...")
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    assert len(embeddings) == len(metadata), f"Mismatch: {len(embeddings)} embeddings vs {len(metadata)} metadata items"

    vector_size = int(embeddings.shape[1]) if len(embeddings.shape) > 1 else 768

    # Check if collection exists; create only if it does NOT exist
    if not client.collection_exists(COLLECTION_NAME):
        print(f"Creating collection '{COLLECTION_NAME}' (size={vector_size}, distance=COSINE)...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists. Preserving existing collection.")

    print(f"Preparing {len(metadata)} points for Qdrant...")
    points = []
    for embedding, chunk in zip(embeddings, metadata):
        point = qmodels.PointStruct(
            id=chunk["chunk_id"],
            vector=embedding.tolist(),
            payload=chunk,
        )
        points.append(point)

    batches = list(chunk_list(points, BATCH_SIZE))
    print(f"Uploading {len(points)} points to collection '{COLLECTION_NAME}' in {len(batches)} batches of {BATCH_SIZE}...")

    def upload_batch(batch):
        client.upsert(collection_name=COLLECTION_NAME, points=batch)

    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(upload_batch, batch): i for i, batch in enumerate(batches)}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Uploading to Qdrant"):
            try:
                future.result()
            except Exception as e:
                batch_idx = futures[future]
                print(f"\n[ERROR] Batch {batch_idx} failed to upload: {e}")

    print("\nUpload to Qdrant complete!")

    collection_info = client.get_collection(COLLECTION_NAME)
    print("\nCollection Stats:")
    print(collection_info)


if __name__ == "__main__":
    main()
