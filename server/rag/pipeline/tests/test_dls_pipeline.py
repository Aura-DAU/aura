import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add rag directory to path so we can import from pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline


def _build_mocked_pipeline(mock_retriever_class):
    mock_retriever = MagicMock()
    mock_retriever_class.return_value = mock_retriever
    mock_retriever.index = MagicMock()
    mock_retriever.index.query.return_value = {"matches": []}
    mock_retriever.retrieve.return_value = []
    # The dual path now runs a full-query BM25 pass; default it to empty so
    # existing tests exercise the (unchanged) filter/fusion behaviour.
    mock_retriever.bm25.retrieve.return_value = []

    pipeline = RetrievalPipeline()

    pipeline.planner = MagicMock()
    pipeline.planner.plan.return_value = {
        "top_k": 5,
        "entities": {},
        "retrieval_intent": "general",
        "query_decomposition": [],
    }
    pipeline.reranker = MagicMock()
    pipeline.reranker.rerank.return_value = []
    pipeline.rewriter = MagicMock()
    return pipeline, mock_retriever


@patch("pipeline.retrieval.query_rewriter.QueryRewriter", MagicMock)
@patch("pipeline.retrieval.retrieval_pipeline.Reranker")
@patch("pipeline.retrieval.retrieval_pipeline.QueryPlanner")
@patch("pipeline.retrieval.retrieval_pipeline.Retriever")
def test_pipeline_get_context_applies_dls_filter(
    mock_retriever_class, _mock_planner, _mock_reranker
):
    pipeline, mock_retriever = _build_mocked_pipeline(mock_retriever_class)

    pipeline.get_context("What is the fee?", user_role="student")

    mock_retriever.index.query.assert_called()
    _called_args, called_kwargs = mock_retriever.index.query.call_args
    assert "filter" in called_kwargs
    called_filter = called_kwargs["filter"]
    assert "authorization" in called_filter
    assert "$in" in called_filter["authorization"]
    assert sorted(called_filter["authorization"]["$in"]) == sorted(["public", "student"])


@patch("pipeline.retrieval.query_rewriter.QueryRewriter", MagicMock)
@patch("pipeline.retrieval.retrieval_pipeline.Reranker")
@patch("pipeline.retrieval.retrieval_pipeline.QueryPlanner")
@patch("pipeline.retrieval.retrieval_pipeline.Retriever")
def test_pipeline_get_context_applies_dls_filter_superadmin(
    mock_retriever_class, _mock_planner, _mock_reranker
):
    pipeline, mock_retriever = _build_mocked_pipeline(mock_retriever_class)

    pipeline.get_context("What is the fee?", user_role="superadmin")

    mock_retriever.index.query.assert_called()
    _called_args, called_kwargs = mock_retriever.index.query.call_args
    assert "filter" in called_kwargs
    allowed_roles = called_kwargs["filter"]["authorization"]["$in"]
    assert "superadmin" in allowed_roles
    assert "dean_academic" in allowed_roles


@patch("pipeline.retrieval.query_rewriter.QueryRewriter", MagicMock)
@patch("pipeline.retrieval.retrieval_pipeline.Reranker")
@patch("pipeline.retrieval.retrieval_pipeline.QueryPlanner")
@patch("pipeline.retrieval.retrieval_pipeline.Retriever")
def test_entityless_query_runs_full_query_bm25(
    mock_retriever_class, _mock_planner, _mock_reranker
):
    """Regression: a keyword query that yields no planner entity must still get
    a lexical (BM25) pass on the RAW query, folded into the retrieval pool. Before
    the fix, BM25 only ran per-entity, so entity-less queries ("what are the
    hostel rules", "course policy of EL470") degraded to pure dense search and
    buried the exact document."""
    pipeline, mock_retriever = _build_mocked_pipeline(mock_retriever_class)
    mock_retriever.bm25.retrieve.return_value = [
        {"id": "hostel-1", "score": 1.0, "metadata": {"title": "Hostel Rules"}}
    ]

    pipeline.get_context("what are the hostel rules", user_role="student")

    # BM25 was invoked on the full raw query (no entities extracted here) …
    mock_retriever.bm25.retrieve.assert_called()
    _args, kwargs = mock_retriever.bm25.retrieve.call_args
    assert kwargs["query"] == "what are the hostel rules"
    # … and the same role/scope gating is applied so security is never bypassed.
    lexical_filter = kwargs["metadata_filter"]
    assert sorted(lexical_filter["authorization"]["$in"]) == sorted(["public", "student"])
