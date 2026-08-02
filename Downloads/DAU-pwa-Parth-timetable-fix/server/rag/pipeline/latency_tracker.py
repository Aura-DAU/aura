import contextvars
import time
from contextlib import contextmanager

# Request-scoped timing storage
_latency_data = contextvars.ContextVar("latency_data", default=None)

@contextmanager
def track_segment(segment_name: str):
    data = _latency_data.get()
    t0 = time.time()
    try:
        yield
    finally:
        duration = time.time() - t0
        if data is not None:
            data[segment_name] = data.get(segment_name, 0.0) + duration
        try:
            from api.metrics import STAGE_LATENCY, RAG_STAGE_LATENCY
            STAGE_LATENCY.labels(stage=segment_name).observe(duration)
            RAG_STAGE_LATENCY.labels(stage=segment_name).observe(duration)
        except Exception:
            pass

def init_tracker():
    data = {
        "guardrail_time": 0.0,
        "planner_time": 0.0,
        "embedding_time": 0.0,
        "retrieval_time": 0.0,
        "reranker_time": 0.0,
        "prompt_assembly_time": 0.0,
        "inference_router_time": 0.0,
        "generation_time": 0.0,
        "streaming_time": 0.0,
        "total_time": 0.0
    }
    token = _latency_data.set(data)
    return data, token

def reset_tracker(token):
    _latency_data.reset(token)
