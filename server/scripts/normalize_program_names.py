"""One-off remediation: canonicalize program_name metadata everywhere.

Ingestion (pre-fix) wrote raw regex-extracted programme strings ('B Tech',
'MTech ICT', 'Ph D', OCR junk sentences...) while retrieval filters on
canonical names like "B.Tech. (ICT)". This script rewrites both stores to
the canonical spellings:

  1. metadata.json (BM25 store) — patched in place, timestamped .bak first.
  2. Qdrant payloads — set_payload for canonicalized values, delete_payload
     for program_name values that canonicalize to nothing.

Modeled on normalize_course_codes.py (PR #320).

Usage:
    python normalize_program_names.py [path/to/metadata.json]

Env: QDRANT_URL (default http://localhost:6333), QDRANT_COLLECTION
(default aura_documents). Set SKIP_QDRANT=1 to only patch metadata.json.
"""

import json
import os
import shutil
import sys
import time
from collections import Counter

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(
    0,
    os.path.join(_SCRIPT_DIR, "..", "rag", "pipeline", "ingestion", "chunking"),
)
from program_names import canonicalize_program_value  # noqa: E402

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_SCRIPT_DIR, "..", ".env"))
except ImportError:
    pass

DEFAULT_METADATA_PATH = os.path.join(
    _SCRIPT_DIR, "..", "rag", "pipeline", "vector_store", "metadata.json"
)


def _distinct_values(chunks):
    values = Counter()
    for chunk in chunks:
        val = chunk.get("program_name")
        if not val:
            continue
        for v in (val if isinstance(val, list) else [val]):
            values[str(v)] += 1
    return values


def patch_metadata(metadata_path):
    print(f"Loading metadata from {metadata_path}...")
    with open(metadata_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    before = _distinct_values(chunks)
    print(f"Before: {len(chunks)} chunks, {len(before)} distinct program_name values")

    rewritten = 0
    removed = 0
    for chunk in chunks:
        if "program_name" not in chunk:
            continue
        raw = chunk["program_name"]
        canonical = canonicalize_program_value(raw)
        if canonical is None:
            del chunk["program_name"]
            removed += 1
        elif canonical != raw:
            chunk["program_name"] = canonical
            rewritten += 1

    backup_path = f"{metadata_path}.{time.strftime('%Y%m%d-%H%M%S')}.bak"
    shutil.copy2(metadata_path, backup_path)
    print(f"Backup written to {backup_path}")

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False)

    after = _distinct_values(chunks)
    print(f"metadata.json: rewrote {rewritten}, removed {removed} program_name values")
    print(f"After: {len(after)} distinct program_name values:")
    for value, count in after.most_common():
        print(f"  {count:6d}  {value}")
    return chunks


def patch_qdrant():
    from qdrant_client import QdrantClient

    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "aura_documents")

    print(f"Connecting to Qdrant at {qdrant_url}...")
    try:
        client = QdrantClient(url=qdrant_url)
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")
        sys.exit(1)

    print(f"Scrolling points in collection: {collection_name}")

    has_more = True
    next_page_offset = None
    updated_count = 0
    deleted_count = 0
    total_processed = 0

    while has_more:
        points, next_page_offset = client.scroll(
            collection_name=collection_name,
            limit=1000,
            offset=next_page_offset,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            total_processed += 1
            payload = point.payload

            if not payload or "program_name" not in payload:
                continue

            raw = payload["program_name"]
            canonical = canonicalize_program_value(raw)

            if canonical is None:
                client.delete_payload(
                    collection_name=collection_name,
                    keys=["program_name"],
                    points=[point.id],
                )
                deleted_count += 1
            elif canonical != raw:
                client.set_payload(
                    collection_name=collection_name,
                    payload={"program_name": canonical},
                    points=[point.id],
                )
                updated_count += 1

        if next_page_offset is None:
            has_more = False

    print(
        f"Qdrant: processed {total_processed} points, "
        f"updated {updated_count}, removed program_name on {deleted_count}"
    )


def main():
    metadata_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_METADATA_PATH
    metadata_path = os.path.abspath(metadata_path)
    patch_metadata(metadata_path)

    if os.getenv("SKIP_QDRANT"):
        print("SKIP_QDRANT set — skipping Qdrant payload patch.")
        return
    patch_qdrant()
    print("Finished!")


if __name__ == "__main__":
    main()
