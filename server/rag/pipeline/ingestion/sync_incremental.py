import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
import torch
import hashlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
logger = logging.getLogger(__name__)

# Setup directories
INGESTION_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(INGESTION_DIR))
sys.path.insert(0, str(INGESTION_DIR / "chunking"))

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

    # 2. Embed only new chunks via TEI
    new_embeddings = None
    if new_chunks:
        embedding_url = os.getenv("EMBEDDING_URL", "http://10.100.97.74:8081")
        tei_endpoint = f"{embedding_url.rstrip('/')}/embed"
        texts = [c["text"] for c in new_chunks]
        logger.info("Generating embeddings for %d new chunks via TEI (%s)...", len(texts), tei_endpoint)

        all_embeddings = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload = {"inputs": batch, "truncate": True}
            res = requests.post(tei_endpoint, json=payload, headers={"Content-Type": "application/json"})
            res.raise_for_status()
            all_embeddings.extend(res.json())

        new_embeddings = np.array(all_embeddings, dtype="float32")
        norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        new_embeddings = (new_embeddings / np.maximum(norms, 1e-12)).astype("float32")

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
    qdrant_url = os.getenv("QDRANT_URL", "http://10.100.97.74:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "aura_documents")
    api_key = os.getenv("QDRANT_API_KEY") or None

    logger.info("Connecting to Qdrant at %s...", qdrant_url)
    qclient = QdrantClient(url=qdrant_url, api_key=api_key)

    if not qclient.collection_exists(collection_name):
        logger.info("Creating Qdrant collection %s (768-dim, COSINE)...", collection_name)
        qclient.create_collection(
            collection_name=collection_name,
            vectors_config=qmodels.VectorParams(size=768, distance=qmodels.Distance.COSINE),
        )

    # Delete old vectors for modified files from Qdrant
    if updated_files:
        logger.info("Deleting old vectors from Qdrant for %d modified files...", len(updated_files))
        for f, canonical_path in updated_files:
            import uuid
            doc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f.as_posix()))
            try:
                qclient.delete(
                    collection_name=collection_name,
                    points_selector=qmodels.FilterSelector(
                        filter=qmodels.Filter(
                            must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=doc_id))]
                        )
                    ),
                )
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
                    qclient.delete(
                        collection_name=collection_name,
                        points_selector=qmodels.FilterSelector(
                            filter=qmodels.Filter(
                                must=[qmodels.FieldCondition(key="document_id", match=qmodels.MatchValue(value=doc_id))]
                            )
                        ),
                    )
                    logger.info("  Deleted vectors for: %s (doc_id: %s)", canonical_path, doc_id)
                except Exception as e:
                    logger.error("Failed to delete vectors for %s from Qdrant: %s", canonical_path, e)

    if new_chunks:
        logger.info("Preparing points for Qdrant upload...")
        points = []
        for embedding, chunk in zip(new_embeddings, new_chunks):
            point = qmodels.PointStruct(
                id=chunk["chunk_id"],
                vector=embedding.tolist(),
                payload=chunk,
            )
            points.append(point)

        batch_size = 100
        logger.info("Uploading %d new points to Qdrant collection %s in batches of %d...", len(points), collection_name, batch_size)
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            qclient.upsert(collection_name=collection_name, points=batch)
        logger.info("Qdrant upload complete.")

    # 5. Refresh entity index
    logger.info("Rebuilding entity index...")
    build_entity_index(METADATA_FILE, ENTITY_INDEX_FILE)

    logger.info("INCREMENTAL SYNC COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    main()

