# build_entity_index.py
# Offline one-time script implementing Step 2 of the professor's algorithm:
# python pipeline/ingestion/build_entity_index.py

import json
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s — %(message)s"
)
logger = logging.getLogger(__name__)

# ── Paths ─────────────────────────────────────────────────────────────────────

PIPELINE_DIR = Path(__file__).resolve().parent.parent
VECTOR_STORE_DIR = PIPELINE_DIR / "vector_store"
METADATA_PATH = VECTOR_STORE_DIR / "metadata.json"
ENTITY_INDEX_PATH = VECTOR_STORE_DIR / "entity_index.json"

# Entity fields we index.  Add new fields here as the corpus grows.
ENTITY_FIELDS = [
    "faculty_name",
    "course_code",
    "program_name",
    "event_name",
    "semester",
]


# ── Builder ───────────────────────────────────────────────────────────────────

def build_entity_index(metadata_path: Path, output_path: Path) -> dict:
    # Read all chunks from metadata_path and build an inverted entity index.
    # Returns the index dict so callers can inspect it without touching disk.
    if not metadata_path.exists():
        raise FileNotFoundError(
            f"metadata.json not found at {metadata_path}. "
            "Run sync_db.py first to generate it."
        )

    with open(metadata_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logger.info("Loaded %d chunks from %s", len(chunks), metadata_path)

    # entity_index[field][entity_value] = [chunk_id, chunk_id, ...]
    entity_index: dict[str, dict[str, list[str]]] = {
        field: {} for field in ENTITY_FIELDS
    }

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id:
            continue

        for field in ENTITY_FIELDS:
            value = chunk.get(field)

            if not value:
                continue

            # Normalise: strip whitespace; skip empty strings / None / null
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
                values = [value]
            elif isinstance(value, list):
                values = [str(v).strip() for v in value if v]
            else:
                values = [str(value).strip()]

            for v in values:
                if v not in entity_index[field]:
                    entity_index[field][v] = []
                if chunk_id not in entity_index[field][v]:
                    entity_index[field][v].append(chunk_id)

    # ── Stats ─────────────────────────────────────────────────────────────
    for field, mapping in entity_index.items():
        logger.info(
            "  %-20s -> %d unique entity values, %d total mappings",
            field,
            len(mapping),
            sum(len(ids) for ids in mapping.values()),
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(entity_index, f, indent=2, ensure_ascii=False)

    logger.info("Entity index written to %s", output_path)
    return entity_index


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    build_entity_index(METADATA_PATH, ENTITY_INDEX_PATH)
