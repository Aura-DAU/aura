from __future__ import annotations

import sys
from pathlib import Path

_rag_dir = str(Path(__file__).resolve().parent.parent / "rag")
if _rag_dir not in sys.path:
    sys.path.insert(0, _rag_dir)

from pipeline.query_logger import (
    classify_query_outcome,
    normalize_sources_for_trace,
    record_query_trace_sync,
    record_query_trace_async,
)

__all__ = [
    "classify_query_outcome",
    "normalize_sources_for_trace",
    "record_query_trace_sync",
    "record_query_trace_async",
]
