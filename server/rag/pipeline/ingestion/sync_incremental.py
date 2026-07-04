import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import torch

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Setup directories
INGESTION_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INGESTION_DIR / "chunking"))

from config import MODEL_NAME
from process_corpus import process_markdown_file
from build_entity_index import build_entity_index

DATA_DIR = INGESTION_DIR.parent.parent.parent.parent / "data"
VECTOR_STORE_DIR = INGESTION_DIR.parent / "vector_store"
METADATA_FILE = VECTOR_STORE_DIR / "metadata.json"
EMBEDDINGS_FILE = VECTOR_STORE_DIR / "embeddings.npy"
ENTITY_INDEX_FILE = VECTOR_STORE_DIR / "entity_index.json"

def main():
    load_dotenv()
    
    if not METADATA_FILE.exists() or not EMBEDDINGS_FILE.exists():
        logger.error("Full index metadata or embeddings files not found. Run sync_db.py first to create base files.")
        sys.exit(1)

    logger.info("Loading existing metadata...")
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    existing_files = {chunk.get("source_file") for chunk in metadata if chunk.get("source_file")}
    logger.info("Found %d chunks representing %d unique files in current index.", len(metadata), len(existing_files))

    logger.info("Scanning directory: %s", DATA_DIR)
    md_files = list(DATA_DIR.rglob("*.md"))
    new_files = [f for f in md_files if f.name not in existing_files]

    if not new_files:
        logger.info("No new markdown files found. Database is up to date!")
        sys.exit(0)

    logger.info("Found %d new files to process:", len(new_files))
    for f in new_files:
        logger.info("  - %s", f.relative_to(DATA_DIR))

    # 1. Chunk only new files
    new_chunks = []
    for md_file in new_files:
        try:
            chunks = process_markdown_file(md_file)
            new_chunks.extend(chunks)
            logger.info("Processed %s -> %d chunks", md_file.name, len(chunks))
        except Exception as e:
            logger.error("Failed to chunk %s: %s", md_file, e)

    if not new_chunks:
        logger.warning("No new chunks generated. Exiting.")
        sys.exit(0)

    # 2. Embed only new chunks
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    logger.info("Loading embedding model %s on device: %s...", MODEL_NAME, device)
    model = SentenceTransformer(MODEL_NAME, device=device)

    texts = [c["text"] for c in new_chunks]
    logger.info("Generating embeddings for %d new chunks...", len(texts))
    new_embeddings = model.encode(
        texts,
        batch_size=128,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    ).astype("float32")

    # 3. Concatenate and save local vector store files
    logger.info("Saving updated local embeddings and metadata...")
    old_embeddings = np.load(EMBEDDINGS_FILE)
    updated_embeddings = np.concatenate((old_embeddings, new_embeddings), axis=0)
    
    np.save(EMBEDDINGS_FILE, updated_embeddings)

    metadata.extend(new_chunks)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    # 4. Upload new chunks to Pinecone
    api_key = os.getenv("PINECONE_API_KEY")
    index_name = os.getenv("PINECONE_INDEX")
    if not api_key or not index_name:
        logger.error("PINECONE_API_KEY or PINECONE_INDEX not set in environment.")
        sys.exit(1)

    logger.info("Connecting to Pinecone...")
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)

    logger.info("Preparing vectors for Pinecone upload...")
    vectors = []
    for embedding, chunk in zip(new_embeddings, new_chunks):
        vector = {
            "id": chunk["chunk_id"],
            "values": embedding.tolist(),
            "metadata": {
                "text": chunk["text"],
                "cluster": chunk.get("cluster"),
                "subclusters": chunk.get("subclusters"),
                "document_type": chunk.get("document_type")
            }
        }
        
        # Coordinate metadata
        if chunk.get("document_id"):
            vector["metadata"]["document_id"] = chunk["document_id"]
        if chunk.get("chunk_index") is not None:
            vector["metadata"]["chunk_index"] = int(chunk["chunk_index"])
        if chunk.get("total_chunks") is not None:
            vector["metadata"]["total_chunks"] = int(chunk["total_chunks"])

        # Optional metadata fields
        for field in ["category", "title", "url", "faculty_name", "program_name", "section_type", "event_name", "event_date", "venue", "semester", "course_code", "course_name", "course_type", "credits", "h1", "h2", "h3", "scraped_date", "authorization"]:
            if chunk.get(field) is not None:
                vector["metadata"][field] = chunk[field]

        vectors.append(vector)

    # Upload in partitioned batches (recommended batch size is <= 200)
    batch_size = 200
    logger.info("Uploading %d new vectors to Pinecone index %s in batches of %d...", len(vectors), index_name, batch_size)
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=batch)
    logger.info("Pinecone upload complete.")

    # 5. Refresh entity index
    logger.info("Rebuilding entity index...")
    build_entity_index(METADATA_FILE, ENTITY_INDEX_FILE)

    logger.info("INCREMENTAL SYNC COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
