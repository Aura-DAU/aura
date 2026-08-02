# AURA RAG package. Prefer ``from rag import AURA`` with ``PYTHONPATH=server``.
# Lazy export so importing ``rag`` (or pipeline tests) does not load Pinecone.

from typing import Any

__all__ = ["AURA"]


def __getattr__(name: str) -> Any:
    if name == "AURA":
        from .rag import AURA as _AURA
        return _AURA
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
