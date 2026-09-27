"""Load-handling fixes: pooled HTTP sessions (not one connection per call)
and lock-guarded lazy loading of local-model fallbacks, so a burst of
concurrent requests during a remote-service outage can't race to build
several copies of the same multi-hundred-MB model at once."""

import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from pipeline.retrieval import reranker as rr
from pipeline.retrieval import retriever as rt


def _ok_response(payload):
    return SimpleNamespace(status_code=200, json=lambda: payload)


# ── Pooled sessions: one Session object, reused, not one-per-call ────────

def test_embed_query_reuses_one_session_across_many_calls(monkeypatch):
    monkeypatch.setattr(rt, "_embed_session", None)  # isolate from other tests
    monkeypatch.setenv("EMBEDDING_SERVICE_URL", "http://embed.test")
    created = []

    class FakeSession:
        def __init__(self):
            created.append(self)
            self.calls = 0

        def post(self, *a, **k):
            self.calls += 1
            return _ok_response({"embeddings": [[0.1, 0.2]]})

        def mount(self, *a, **k):
            pass

    monkeypatch.setattr("requests.Session", FakeSession)
    retriever = rt.Retriever.__new__(rt.Retriever)
    for _ in range(5):
        retriever.embed_query("hostel fee")
    assert len(created) == 1, "a new Session must not be built per call"
    assert created[0].calls == 5


def test_embed_session_pool_size_is_env_tunable(monkeypatch):
    monkeypatch.setattr(rt, "_embed_session", None)
    monkeypatch.setenv("EMBED_HTTP_POOL_SIZE", "7")
    import importlib
    importlib.reload(rt)
    try:
        assert rt.EMBED_HTTP_POOL_SIZE == 7
        session = rt._get_embed_session()
        adapter = session.get_adapter("http://embed.test")
        assert adapter._pool_maxsize == 7
    finally:
        importlib.reload(rt)  # restore default env for later tests


def test_rerank_reuses_one_session_across_many_calls(monkeypatch):
    monkeypatch.setattr(rr, "_rerank_session", None)
    monkeypatch.setenv("RERANKER_SERVICE_URL", "http://rerank.test")
    created = []

    class FakeSession:
        def __init__(self):
            created.append(self)
            self.calls = 0

        def post(self, *a, **k):
            self.calls += 1
            return _ok_response({"scores": [1.0, 2.0]})

        def mount(self, *a, **k):
            pass

    monkeypatch.setattr("requests.Session", FakeSession)
    reranker = rr.Reranker.__new__(rr.Reranker)
    reranker.H1_BOOST, reranker.H2_BOOST, reranker.H3_BOOST = 0.1, 0.2, 0.15
    for _ in range(4):
        reranker.rerank("q", [
            {"id": 1, "metadata": {"text": "a"}},
            {"id": 2, "metadata": {"text": "b"}},
        ], {"entities": {}})
    assert len(created) == 1
    assert created[0].calls == 4


# ── No urllib3-level retry stacked under the existing manual retry loop ──

def test_embed_adapter_has_no_extra_retry_layer():
    """The existing EMBED_REMOTE_ATTEMPTS loop is the only retry layer;
    stacking urllib3 retries under it would silently multiply attempts."""
    session = rt._get_embed_session()
    adapter = session.get_adapter("http://embed.test")
    assert adapter.max_retries.total in (0, None) or getattr(adapter.max_retries, "total", 0) == 0


def test_rerank_adapter_has_no_extra_retry_layer():
    session = rr._get_rerank_session()
    adapter = session.get_adapter("http://rerank.test")
    assert adapter.max_retries.total in (0, None) or getattr(adapter.max_retries, "total", 0) == 0


# ── Lazy local-model loads are race-free ──────────────────────────────────

def test_embed_local_model_loaded_exactly_once_under_concurrency(monkeypatch):
    build_calls = []

    def fake_build(name):
        build_calls.append(name)
        time.sleep(0.05)  # widen the race window the lock must close
        return SimpleNamespace(encode=lambda *a, **k: [[0.0]])

    monkeypatch.setattr(rt, "SentenceTransformer", fake_build, raising=False)
    monkeypatch.setitem(
        __import__("sys").modules, "sentence_transformers",
        SimpleNamespace(SentenceTransformer=fake_build),
    )
    retriever = rt.Retriever.__new__(rt.Retriever)
    retriever.model = None

    threads = [threading.Thread(target=retriever._local_model) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(build_calls) == 1, "the local model must be built exactly once, not once per racing thread"


def test_rerank_local_model_loaded_exactly_once_under_concurrency(monkeypatch):
    import sys

    build_calls = []

    class FakeTokenizer:
        @staticmethod
        def from_pretrained(*a, **k):
            build_calls.append("tokenizer")
            time.sleep(0.05)
            return object()

    class FakeModel:
        def to(self, device):
            return self

        def eval(self):
            pass

    class FakeModelCls:
        @staticmethod
        def from_pretrained(*a, **k):
            build_calls.append("model")
            time.sleep(0.05)
            return FakeModel()

    fake_torch = SimpleNamespace(
        device=lambda x: x,
        cuda=SimpleNamespace(is_available=lambda: False),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: False)),
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(
        sys.modules, "transformers",
        SimpleNamespace(
            AutoTokenizer=FakeTokenizer,
            AutoModelForSequenceClassification=FakeModelCls,
        ),
    )

    reranker = rr.Reranker.__new__(rr.Reranker)
    reranker.model = None
    reranker.tokenizer = None
    reranker.device = None

    threads = [threading.Thread(target=reranker._ensure_local_model) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # One load = one tokenizer build + one model build, never more.
    assert build_calls.count("tokenizer") == 1
    assert build_calls.count("model") == 1


def test_already_loaded_model_never_touches_the_lock(monkeypatch):
    """Fast path: an already-loaded model must not block on the lock at all."""
    reranker = rr.Reranker.__new__(rr.Reranker)
    reranker.model, reranker.tokenizer = object(), object()
    reranker._local_model_lock = MagicMock()
    reranker._ensure_local_model()
    reranker._local_model_lock.__enter__.assert_not_called()
