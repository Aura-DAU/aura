import time
from pipeline.latency_tracker import init_tracker, reset_tracker, track_segment, _latency_data

def test_track_segment_accumulation():
    # 1. Initialize the request-scoped tracker
    data, token = init_tracker()
    try:
        # 2. Simulate sequential segment tracking
        with track_segment("guardrail_time"):
            time.sleep(0.01)  # sleep for ~10ms
            
        with track_segment("guardrail_time"):
            time.sleep(0.01)  # sleep for another ~10ms
            
        with track_segment("retrieval_time"):
            time.sleep(0.01)  # sleep for ~10ms
            
        # 3. Assert correct time accumulation
        assert data["guardrail_time"] >= 0.015  # allowing slight CPU scheduling tolerance
        assert data["retrieval_time"] >= 0.008
        assert data["generation_time"] == 0.0
    finally:
        # 4. Cleanup and assert reset behavior
        reset_tracker(token)
        assert _latency_data.get() is None

def test_uninitialized_tracking_fails_safely():
    # Calling track_segment outside of a chat request (uninitialized tracker)
    # should not crash the request, it should fail silently and gracefully.
    try:
        with track_segment("guardrail_time"):
            time.sleep(0.01)
    except Exception as e:
        assert False, f"track_segment raised an exception on uninitialized context: {e}"
