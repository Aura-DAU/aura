import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
from dotenv import load_dotenv
from qdrant_client import models
from sentence_transformers import SentenceTransformer
import torch
import hashlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Setup directories
INGESTION_DIR = Path(__file__).resolve().parent
RAG_DIR = INGESTION_DIR.parent.parent
if str(RAG_DIR) not in sys.path:
    sys.path.insert(0, str(RAG_DIR))
sys.path.insert(0, str(INGESTION_DIR))
sys.path.insert(0, str(INGESTION_DIR / "chunking"))

from config import MODEL_NAME
from process_corpus import process_markdown_file
from build_entity_index import build_entity_index
from pipeline.retrieval.qdrant_adapter import QdrantAdapter

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


    # Helper to convert paths to a canonical format relative to DATA_DIR
    def get_canonical_path(path_str):
        path_str = Path(path_str).as_posix().lower()
        if "data/" in path_str:
            return path_str.split("data/", 1)[1]
        return path_str

    logger.info("Scanning directory: %s", DATA_DIR)
    md_files = list(DATA_DIR.rglob("*.md"))

    # 1. First, pre-calculate hashes of all files on disk
    current_file_hashes = {}
    for f in md_files:
        canonical_path = get_canonical_path(f)
        try:
            with open(f, "r", encoding="utf-8") as file_obj:
                content = file_obj.read()
            current_file_hashes[canonical_path] = hashlib.md5(content.encode("utf-8")).hexdigest()
        except Exception as e:
            logger.error("Failed to read/hash file %s: %s", f, e)

    # 2. Upgrade existing metadata on-the-fly (Backfill missing file_hash keys)
    metadata_updated = False
    for chunk in metadata:
        path = chunk.get("path")
        if path and not chunk.get("file_hash"):
            canonical_path = get_canonical_path(path)
            disk_hash = current_file_hashes.get(canonical_path)
            if disk_hash:
                chunk["file_hash"] = disk_hash
                metadata_updated = True

    if metadata_updated:
        logger.info("Backfilling missing file_hash keys in existing metadata.json...")
        with open(METADATA_FILE, "w", encoding="utf-8") as f_out:
            json.dump(metadata, f_out, ensure_ascii=False)
        logger.info("Local metadata.json migration complete.")

    # 3. Map existing files to their last known hashes
    existing_file_hashes = {}
    for chunk in metadata:
        path = chunk.get("path")
        if path and chunk.get("file_hash"):
            canonical_path = get_canonical_path(path)
            existing_file_hashes[canonical_path] = chunk["file_hash"]

    logger.info("Found %d chunks representing %d unique files in current index.", len(metadata), len(existing_file_hashes))

    new_files = []
    updated_files = []

    # 4. Check each file for changes
    for f in md_files:
        canonical_path = get_canonical_path(f)
        current_hash = current_file_hashes.get(canonical_path)
        if not current_hash:
            continue

        if canonical_path not in existing_file_hashes:
            # Completely new file
            new_files.append(f)
        elif existing_file_hashes[canonical_path] != current_hash:
            # Existing file that was modified
            updated_files.append((f, canonical_path))

    # 5. Check for deleted files (exist in index but no longer on disk)
    current_canonical_paths = {get_canonical_path(f) for f in md_files}
    deleted_path_to_doc_id = {}
    for chunk in metadata:
        path = chunk.get("path")
        if path:
            canonical_path = get_canonical_path(path)
            if canonical_path not in current_canonical_paths:
                deleted_path_to_doc_id[canonical_path] = chunk.get("document_id")

    deleted_files = list(deleted_path_to_doc_id.keys())

    # Combine both lists as files that need processing
    files_to_process = new_files + [f for f, _ in updated_files]

    if not files_to_process and not deleted_files:
        logger.info("No new, modified, or deleted markdown files found. Database is up to date!")
        sys.exit(0)

    if new_files:
        logger.info("Found %d new files to process:", len(new_files))
        for f in new_files:
            logger.info("  - [NEW] %s", f.relative_to(DATA_DIR))
            
    if updated_files:
        logger.info("Found %d modified files to update:", len(updated_files))
        for f, _ in updated_files:
            logger.info("  - [MODIFIED] %s", f.relative_to(DATA_DIR))

    if deleted_files:
        logger.info("Found %d deleted files to remove:", len(deleted_files))
        for f in deleted_files:
            logger.info("  - [DELETED] %s", f)

    # 1. Chunk only modified/new files
    new_chunks = []
    for md_file in files_to_process:
        try:
            chunks = process_markdown_file(md_file)
            new_chunks.extend(chunks)
            logger.info("Processed %s -> %d chunks", md_file.name, len(chunks))
        except Exception as e:
            logger.error("Failed to chunk %s: %s", md_file, e)

    if not new_chunks and not deleted_files:
        logger.warning("No new chunks generated and no files to delete. Exiting.")
        sys.exit(0)

    # 2. Embed only new chunks
    new_embeddings = None
    vectors = []
    if new_chunks:
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

    # 3. Clean local metadata & embeddings for updated/deleted files first
    if updated_files or deleted_files:
        logger.info("Removing old chunks for %d updated/deleted files from local index...", len(updated_files) + len(deleted_files))
        files_to_remove = {canonical_path for _, canonical_path in updated_files} | set(deleted_files)
        
        keep_indices = []
        for idx, chunk in enumerate(metadata):
            path = chunk.get("path")
            if path and get_canonical_path(path) in files_to_remove:
                continue
            keep_indices.append(idx)
            
        metadata = [metadata[idx] for idx in keep_indices]
        
        old_embeddings = np.load(EMBEDDINGS_FILE)
        old_embeddings = old_embeddings[keep_indices]
        np.save(EMBEDDINGS_FILE, old_embeddings)

    # Save updated local embeddings and metadata
    logger.info("Saving updated local embeddings and metadata...")
    if new_embeddings is not None:
        old_embeddings = np.load(EMBEDDINGS_FILE)
        updated_embeddings = np.concatenate((old_embeddings, new_embeddings), axis=0)
        np.save(EMBEDDINGS_FILE, updated_embeddings)
        metadata.extend(new_chunks)
    
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    # 4. Upload new chunks to Qdrant
    try:
        vector_store = QdrantAdapter()
    except ValueError as e:
        logger.error("Qdrant configuration error: %s", e)
        sys.exit(1)

    # Delete old vectors for modified files from Qdrant
    if updated_files:
        logger.info("Deleting old vectors from Qdrant for %d modified files...", len(updated_files))
        for f, canonical_path in updated_files:
            import uuid
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f.as_posix()))
            try:
                vector_store.delete_by_filter({"document_id": {"$eq": doc_id}})
                logger.info("  Deleted old vectors for: %s", canonical_path)
            except Exception as e:
                logger.error("Failed to delete vectors for %s from Qdrant: %s", canonical_path, e)

    # Delete vectors for deleted files from Qdrant
    if deleted_files:
        logger.info("Deleting vectors from Qdrant for %d deleted files...", len(deleted_files))
        for canonical_path in deleted_files:
            doc_id = deleted_path_to_doc_id.get(canonical_path)
            if doc_id:
                try:
                    vector_store.delete_by_filter({"document_id": {"$eq": doc_id}})
                    logger.info("  Deleted vectors for: %s (doc_id: %s)", canonical_path, doc_id)
                except Exception as e:
                    logger.error("Failed to delete vectors for %s from Qdrant: %s", canonical_path, e)

    if new_chunks:
        logger.info("Preparing vectors for Qdrant upload...")
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
            for field in ["category", "title", "url", "faculty_name", "program_name", "section_type", "event_name", "event_date", "venue", "semester", "course_code", "course_name", "course_type", "credits", "h1", "h2", "h3", "scraped_date", "authorization", "start_line", "end_line", "document_year"]:
                if chunk.get(field) is not None:
                    if field in ("start_line", "end_line"):
                        vector["metadata"][field] = int(chunk[field])
                    elif field == "document_year":
                        try:
                            vector["metadata"][field] = int(chunk[field])
                        except (ValueError, TypeError):
                            vector["metadata"][field] = str(chunk[field])
                    else:
                        vector["metadata"][field] = chunk[field]

            vectors.append(
                models.PointStruct(
                    id=vector["id"],
                    vector=vector["values"],
                    payload=vector["metadata"],
                )
            )

    # Upload in partitioned batches (recommended batch size is <= 200)
    batch_size = 200
    logger.info("Uploading %d new vectors to Qdrant collection %s in batches of %d...", len(vectors), vector_store.collection_name, batch_size)
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        vector_store.upsert(batch)
    logger.info("Qdrant upload complete.")

    # 5. Refresh entity index
    logger.info("Rebuilding entity index...")
    build_entity_index(METADATA_FILE, ENTITY_INDEX_FILE)

    logger.info("INCREMENTAL SYNC COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
