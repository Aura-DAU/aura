"""
upload_to_qdrant.py — Phase A migration: replaces upload_to_pinecone.py.

Same metadata payload as the Pinecone version (field-for-field, including
the `relative_path`/`start_line`/`end_line` added for the citation
side-drawer) — only the destination client changed. Ensures the target
collection exists (cosine distance, sized to the embedding model's output
dim) before upserting.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from tqdm import tqdm


# ==================================================
# CONFIG
# ==================================================

EMBEDDINGS_FILE = "../../vector_store/embeddings.npy"
METADATA_FILE = "../../vector_store/metadata.json"

BATCH_SIZE = 100


# ==================================================
# HELPERS
# ==================================================

def chunk_list(items, batch_size):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def build_payload(chunk: dict) -> dict:
    payload = {
        "text": chunk["text"],
        "cluster": chunk.get("cluster"),
        "subclusters": chunk.get("subclusters"),
        "document_type": chunk.get("document_type"),
    }

    if chunk.get("document_id"):
        payload["document_id"] = chunk["document_id"]
    if chunk.get("chunk_index") is not None:
        payload["chunk_index"] = int(chunk["chunk_index"])
    if chunk.get("total_chunks") is not None:
        payload["total_chunks"] = int(chunk["total_chunks"])

    for field in (
        "category", "title", "url", "faculty_name", "program_name",
        "section_type", "event_name", "event_date", "venue", "semester",
        "course_code", "course_name", "course_type", "credits",
        "h1", "h2", "h3", "scraped_date",
        # Portable path back to the source markdown file, used by the
        # /documents API to power the citation side-drawer viewer.
        "relative_path",
    ):
        if chunk.get(field):
            payload[field] = chunk[field]

    if chunk.get("start_line") is not None:
        payload["start_line"] = int(chunk["start_line"])
    if chunk.get("end_line") is not None:
        payload["end_line"] = int(chunk["end_line"])

    if chunk.get("document_year") is not None:
        try:
            payload["document_year"] = int(chunk["document_year"])
        except (ValueError, TypeError):
            payload["document_year"] = str(chunk["document_year"])

    if chunk.get("authorization"):
        payload["authorization"] = chunk["authorization"]

    return payload


# ==================================================
# MAIN
# ==================================================

def main():
    load_dotenv()

    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY") or None
    collection_name = os.getenv("QDRANT_COLLECTION", "aura-knowledge-base")

    print(f"Connecting to Qdrant at {url}...")
    client = QdrantClient(url=url, api_key=api_key)

    print("Loading embeddings...")
    embeddings = np.load(EMBEDDINGS_FILE)

    print("Loading metadata...")
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    assert len(embeddings) == len(metadata)

    vector_size = int(embeddings.shape[1])
    if not client.collection_exists(collection_name):
        print(f"Creating collection '{collection_name}' (dim={vector_size}, cosine)...")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(size=vector_size, distance=qmodels.Distance.COSINE),
        )

    print(f"Preparing {len(metadata)} points...")
    points = [
        qmodels.PointStruct(
            id=chunk["chunk_id"],  # already a UUID4 string — valid Qdrant point ID
            vector=embedding.tolist(),
            payload=build_payload(chunk),
        )
        for embedding, chunk in zip(embeddings, metadata)
    ]

    batches = list(chunk_list(points, BATCH_SIZE))
    print(f"Uploading {len(points)} points in {len(batches)} batches of {BATCH_SIZE}...")

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(client.upsert, collection_name=collection_name, points=batch): i
            for i, batch in enumerate(batches)
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Uploading"):
            try:
                future.result()
            except Exception as e:
                batch_idx = futures[future]
                print(f"\n[ERROR] Batch {batch_idx} failed to upload: {e}")

    print("\nUpload complete!")

    info = client.get_collection(collection_name)
    print("\nCollection Stats:")
    print(f"  points_count: {info.points_count}")
    print(f"  status: {info.status}")


if __name__ == "__main__":
    main()
