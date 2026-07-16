import pytest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add rag directory to path so we can import from pipeline
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from pipeline.retrieval.retrieval_pipeline import RetrievalPipeline

def test_pipeline_get_context_applies_dls_filter():
    pipeline = RetrievalPipeline()
    
    # Mock retriever
    pipeline.retriever = MagicMock()
    pipeline.retriever.retrieve.return_value = []
    
    # Mock retriever index query response
    pipeline.retriever.index.query.return_value = {"matches": []}
    
    # Mock planner to return a simple plan
    pipeline.planner = MagicMock()
    pipeline.planner.plan.return_value = {
        "top_k": 5,
        "entities": {},
        "retrieval_intent": "general",
        "query_decomposition": []
    }
    
    # Mock reranker
    pipeline.reranker = MagicMock()
    pipeline.reranker.rerank.return_value = []
    
    # Call get_context with student role
    pipeline.get_context("What is the fee?", user_role="student")
    
    # Verify that index.query was called with the correct DLS filter for student
    pipeline.retriever.index.query.assert_called()
    called_args, called_kwargs = pipeline.retriever.index.query.call_args
    assert "filter" in called_kwargs
    called_filter = called_kwargs["filter"]
    assert "authorization" in called_filter
    assert "$in" in called_filter["authorization"]
    assert sorted(called_filter["authorization"]["$in"]) == sorted(["public", "student"])

def test_pipeline_get_context_applies_dls_filter_superadmin():
    pipeline = RetrievalPipeline()
    
    # Mock retriever index query response
    pipeline.retriever = MagicMock()
    pipeline.retriever.index.query.return_value = {"matches": []}
    
    # Mock planner
    pipeline.planner = MagicMock()
    pipeline.planner.plan.return_value = {
        "top_k": 5,
        "entities": {},
        "retrieval_intent": "general",
        "query_decomposition": []
    }
    
    # Mock reranker
    pipeline.reranker = MagicMock()
    pipeline.reranker.rerank.return_value = []
    
    # Call get_context with superadmin role
    pipeline.get_context("What is the fee?", user_role="superadmin")
    
    # Verify that index.query was called with all roles
    pipeline.retriever.index.query.assert_called()
    called_args, called_kwargs = pipeline.retriever.index.query.call_args
    assert "filter" in called_kwargs
    allowed_roles = called_kwargs["filter"]["authorization"]["$in"]
    assert "superadmin" in allowed_roles
    assert "dean_academic" in allowed_roles
