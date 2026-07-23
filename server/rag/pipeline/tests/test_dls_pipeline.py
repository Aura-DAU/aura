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
    assert "authorization" in called_kwargs["filter"]
    assert "$in" in called_kwargs["filter"]["authorization"]
    assert set(called_kwargs["filter"]["authorization"]["$in"]) == {"public", "student"}


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
