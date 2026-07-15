"""Qdrant-specific vector storage operations for the RAG pipeline."""

import os
from typing import Any

from qdrant_client import QdrantClient, models


class QdrantAdapter:
    """Keep Qdrant APIs and filter translation outside retrieval logic."""

    def __init__(self) -> None:
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        self.collection_name = os.getenv("QDRANT_COLLECTION", "aura-documents")

        if not url:
            raise ValueError("QDRANT_URL not found")
        if not api_key:
            raise ValueError("QDRANT_API_KEY not found")

        self.client = QdrantClient(url=url, api_key=api_key)

    @classmethod
    def to_filter(cls, metadata_filter: dict[str, Any] | None) -> models.Filter | None:
        if not metadata_filter:
            return None

        def clause(value: dict[str, Any]) -> models.Filter | models.FieldCondition:
            if "$and" in value:
                return models.Filter(must=[clause(item) for item in value["$and"]])
            if "$or" in value:
                return models.Filter(should=[clause(item) for item in value["$or"]])

            conditions = []
            for key, condition in value.items():
                if "$eq" in condition:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=condition["$eq"]),
                        )
                    )
                elif "$in" in condition:
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            match=models.MatchAny(any=condition["$in"]),
                        )
                    )
                else:
                    raise ValueError(f"Unsupported metadata filter condition for {key}")

            if len(conditions) == 1:
                return conditions[0]
            return models.Filter(must=conditions)

        translated = clause(metadata_filter)
        return translated if isinstance(translated, models.Filter) else models.Filter(must=[translated])

    def search(
        self,
        vector: list[float],
        limit: int,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            query_filter=self.to_filter(metadata_filter),
            with_payload=True,
            with_vectors=False,
        )
        return [
            {
                "id": str(point.id),
                "score": point.score,
                "cosine_score": point.score,
                "metadata": point.payload or {},
            }
            for point in response.points
        ]

    def upsert(self, points: list[models.PointStruct]) -> None:
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )

    def delete_by_filter(self, metadata_filter: dict[str, Any]) -> None:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(filter=self.to_filter(metadata_filter)),
            wait=True,
        )

    def collection_info(self) -> Any:
        return self.client.get_collection(collection_name=self.collection_name)
