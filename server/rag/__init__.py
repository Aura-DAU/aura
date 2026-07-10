"""AURA RAG package.

Prefer ``from rag import AURA`` with ``PYTHONPATH=server``.
When ``server/rag`` is also on ``sys.path`` (legacy flat imports),
``rag.py`` may load as a top-level module instead of this package.
"""

from .rag import AURA

__all__ = ["AURA"]
