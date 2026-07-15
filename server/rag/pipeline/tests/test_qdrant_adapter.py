from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from qdrant_client import models

from pipeline.retrieval.qdrant_adapter import QdrantAdapter


def test_to_filter_translates_equality_and_membership() -> None:
    translated = QdrantAdapter.to_filter(
        {
            "$and": [
                {"course_code": {"$eq": "CS101"}},
                {"authorization": {"$in": ["public", "student"]}},
            ]
        }
    )

    assert isinstance(translated, models.Filter)
    assert len(translated.must) == 2
    assert translated.must[0].key == "course_code"
    assert translated.must[0].match.value == "CS101"
    assert translated.must[1].key == "authorization"
    assert translated.must[1].match.any == ["public", "student"]


def test_search_preserves_internal_retrieval_result_contract() -> None:
    adapter = object.__new__(QdrantAdapter)
    adapter.collection_name = "aura-documents"
    adapter.client = type(
        "Client",
        (),
        {
            "query_points": lambda *_args, **_kwargs: type(
                "Response",
                (),
                {"points": [type("Point", (), {"id": "chunk-1", "score": 0.91, "payload": {"text": "A"}})()]},
            )()
        },
    )()

    results = adapter.search([0.1, 0.2], limit=1)

    assert results == [{"id": "chunk-1", "score": 0.91, "cosine_score": 0.91, "metadata": {"text": "A"}}]
