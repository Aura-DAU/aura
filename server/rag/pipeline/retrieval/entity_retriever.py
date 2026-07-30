# entity_retriever.py
# Implements Step 2→3 of the professor's algorithm:
# retrieval_pipeline.py to form the unified "chunk pool" before reranking.

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Entity fields checked in priority order (same as ENTITY_FIELDS in builder)
ENTITY_FIELDS = [
    "faculty_name",
    "course_code",
    "program_name",
    "event_name",
    "semester",
]

# Fix #2: separate per-field and total caps so that a single high-cardinality
# field (e.g. faculty_name with many chunks) cannot starve other fields.
MAX_ENTITY_CHUNKS_PER_FIELD = 8   # max chunks pulled per individual field
MAX_ENTITY_CHUNKS_TOTAL = 24      # hard cap on the combined pool


class EntityRetriever:
    # Retrieves chunks by matching query entities against the pre-built
    # entity index.  Uses the same metadata store as BM25Retriever so no
    # extra I/O is needed at query time after initialisation.

    def __init__(self, metadata_path: str):
        # Parameters
        # metadata_path : str
        # entity_index.json is expected in the same directory.
        metadata_path = Path(metadata_path)
        entity_index_path = metadata_path.parent / "entity_index.json"

        # ── Load chunk metadata ────────────────────────────────────────────
        with open(metadata_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        # Fast O(1) lookup: chunk_id → full chunk record
        self._chunk_map: dict[str, dict] = {
            chunk["chunk_id"]: chunk
            for chunk in chunks
            if chunk.get("chunk_id")
        }

        # ── Load entity index ──────────────────────────────────────────────
        if not entity_index_path.exists():
            logger.warning(
                "entity_index.json not found at %s. "
                "Run build_entity_index.py to enable entity-based retrieval.",
                entity_index_path,
            )
            self._entity_index: dict[str, dict[str, list[str]]] = {}
        else:
            with open(entity_index_path, "r", encoding="utf-8") as f:
                self._entity_index = json.load(f)
            total = sum(
                len(ids)
                for field_map in self._entity_index.values()
                for ids in field_map.values()
            )
            logger.info(
                "EntityRetriever loaded index with %d total mappings from %s",
                total,
                entity_index_path,
            )

        # Lowercased mirror of the index so case-insensitive fallback lookups
        # are O(1) instead of a linear scan over every key in the field map.
        # setdefault keeps the FIRST key on case-collisions, matching the old
        # scan's first-match-wins behaviour.
        self._entity_index_lower: dict[str, dict[str, list[str]]] = {}
        for field, field_map in self._entity_index.items():
            lower_map: dict[str, list[str]] = {}
            for key, ids in field_map.items():
                lower_map.setdefault(key.lower(), ids)
            self._entity_index_lower[field] = lower_map

    # ── Public API ─────────────────────────────────────────────────────────

    def retrieve_by_entities(
        self,
        entities: dict,
        max_chunks_per_field: int = MAX_ENTITY_CHUNKS_PER_FIELD,
        max_chunks_total: int = MAX_ENTITY_CHUNKS_TOTAL,
        allowed_roles: list[str] = None,
        academic_scope=None,
    ) -> list[dict]:
        # Return chunk records whose entity fields overlap with `entities`.
        # Fix #2: each entity field gets its own independent budget
        # the cross-encoder reranker will assign the real score.
        if not self._entity_index or not entities:
            return []

        # Collect candidate chunk IDs per field, then merge — so each field
        # is always consulted independently up to its own budget.
        # Collect candidate chunk IDs (ordered, deduped via seen set)
        seen: set[str] = set()
        candidate_ids: list[str] = []

        for field in ENTITY_FIELDS:
            if len(candidate_ids) >= max_chunks_total:
                break

            value = entities.get(field)
            if not value:
                continue

            # Normalise to list
            if isinstance(value, str):
                values = [value.strip()]
            elif isinstance(value, list):
                values = [str(v).strip() for v in value if v]
            else:
                values = [str(value).strip()]

            field_map = self._entity_index.get(field, {})

            # Per-field counter resets for every new field (fix #2 core change)
            field_count = 0

            for v in values:
                matched_ids = field_map.get(v, [])

                # Also try case-insensitive fallback (precomputed lower index)
                if not matched_ids:
                    matched_ids = self._entity_index_lower.get(field, {}).get(
                        v.lower(), []
                    )

                for chunk_id in matched_ids:
                    if field_count >= max_chunks_per_field:
                        break
                    if len(candidate_ids) >= max_chunks_total:
                        break

                    # Fix ER1: the second `if chunk_id not in seen` block was
                    # dead code — after the first block runs seen.add(chunk_id),
                    # the second check always evaluates False, so it never
                    # executed. Removed the duplicate to prevent future confusion.
                    if chunk_id not in seen:
                        seen.add(chunk_id)
                        candidate_ids.append(chunk_id)
                        field_count += 1

        # Hydrate to full chunk records
        results = []
        for chunk_id in candidate_ids:
            chunk = self._chunk_map.get(chunk_id)
            if chunk:
                # DLS authorization check
                if allowed_roles is not None:
                    chunk_auth = chunk.get("authorization", ["public"])
                    if isinstance(chunk_auth, str):
                        chunk_auth = [chunk_auth]
                    if not any(role in allowed_roles for role in chunk_auth):
                        continue
                if academic_scope is not None and not academic_scope.document_is_eligible(chunk):
                    continue
                results.append({
                    "id": chunk_id,
                    # Entity-matched chunks start with a neutral score;
                    # the cross-encoder reranker will score them properly.
                    "score": 0.0,
                    "metadata": chunk,
                })

        logger.debug(
            "EntityRetriever: %d entity-matched chunks for entities %s",
            len(results),
            {k: v for k, v in entities.items() if v},
        )
        return results
