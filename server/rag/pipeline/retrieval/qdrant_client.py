"""
Qdrant adapter — Phase A of the architecture-doc migration (Pinecone → Qdrant).

`QdrantIndexAdapter` exposes the same `.query(vector=, top_k=, include_metadata=,
filter=)` shape that `pinecone.Index` used to, returning
`{"matches": [{"id", "score", "metadata"}, ...]}`. This means every call site
in `retrieval_pipeline.py` (which builds Pinecone-style metadata filters —
`{"field": {"$eq": v}}`, `{"field": {"$in": [v1, v2]}}`, `{"$and": [...]}`)
keeps working completely unchanged; only `retriever.py`'s client
construction needed to change. `_translate_filter()` below is what makes
that possible — it walks the same filter dict shape and produces the
equivalent `qdrant_client.models.Filter`.
"""

import logging
from typing import Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

logger = logging.getLogger(__name__)


def _translate_condition(field: str, op_value: dict) -> qmodels.Condition:
    if "$eq" in op_value:
        return qmodels.FieldCondition(key=field, match=qmodels.MatchValue(value=op_value["$eq"]))
    if "$in" in op_value:
        return qmodels.FieldCondition(key=field, match=qmodels.MatchAny(any=list(op_value["$in"])))
    raise ValueError(f"Unsupported Pinecone-style filter operator in {op_value!r} for field {field!r}")


def translate_filter(pinecone_filter: Optional[dict]) -> Optional[qmodels.Filter]:
    """Translate a Pinecone-style metadata filter dict into a Qdrant Filter.

    Supports the operator set this codebase actually emits: {"$eq": v},
    {"$in": [v, ...]}, and top-level {"$and": [filter, filter, ...]}. Any
    other Pinecone operator ($or, $ne, $gt, etc.) was never used by
    retrieval_pipeline.py, so it isn't translated here — extend this
    function first if a caller starts emitting one.
    """
    if not pinecone_filter:
        return None

    if "$and" in pinecone_filter:
        must: list[qmodels.Condition] = []
        for sub in pinecone_filter["$and"]:
            sub_filter = translate_filter(sub)
            if sub_filter is None:
                continue
            # A translated sub-clause is itself a Filter(must=[...]) with a
            # single condition (from as_filter()/auth_filter shapes in
            # retrieval_pipeline.py) — flatten it into the outer `must` list.
            if sub_filter.must:
                must.extend(sub_filter.must)
        return qmodels.Filter(must=must) if must else None

    must = [_translate_condition(field, op_value) for field, op_value in pinecone_filter.items()]
    return qmodels.Filter(must=must) if must else None


class QdrantIndexAdapter:
    """Pinecone-`Index`-shaped facade over a Qdrant collection."""

    def __init__(self, client: QdrantClient, collection_name: str):
        self._client = client
        self._collection = collection_name

    def query(self, vector, top_k: int = 10, include_metadata: bool = True, filter: Optional[dict] = None) -> dict:
        query_filter = translate_filter(filter)

        try:
            hits = self._client.search(
                collection_name=self._collection,
                query_vector=vector,
                limit=top_k,
                query_filter=query_filter,
                with_payload=include_metadata,
            )
        except Exception as e:
            logger.warning("Qdrant query failed: %s", e)
            return {"matches": []}

        matches = [
            {
                "id": str(hit.id),
                "score": hit.score,
                "metadata": hit.payload or {},
            }
            for hit in hits
        ]
        return {"matches": matches}


def build_index_adapter() -> Optional[QdrantIndexAdapter]:
    """Constructs the QdrantIndexAdapter from QDRANT_URL/QDRANT_API_KEY/
    QDRANT_COLLECTION env vars, mirroring how retriever.py used to build a
    pinecone.Index from PINECONE_API_KEY/PINECONE_INDEX. Returns None (with
    a warning) if Qdrant can't be reached, matching the old
    "dense search disabled" fallback behaviour so BM25-only search still
    works.
    """
    import os

    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    api_key = os.getenv("QDRANT_API_KEY") or None
    collection = os.getenv("QDRANT_COLLECTION", "aura-knowledge-base")

    try:
        client = QdrantClient(url=url, api_key=api_key)
        client.get_collection(collection)  # raises if missing/unreachable
        logger.info("Qdrant collection '%s' initialized successfully at %s.", collection, url)
        return QdrantIndexAdapter(client, collection)
    except Exception as e:
        logger.warning("Failed to initialize Qdrant collection '%s' at %s: %s. Dense search will be disabled.", collection, url, e)
        return None
