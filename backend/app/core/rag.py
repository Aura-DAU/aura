"""
RAG pipeline: document loading, embedding index construction, and semantic retrieval.

Document format follows the team's system_prompt_v1.md spec:
  - YAML front-matter fields (title, url, category, scraped_by, scraped_date, team)
    are parsed and preserved as metadata for citation.
  - Retrieved docs are injected as:
      <context>
        <doc id="1" title="..." category="..." url="...">content</doc>
        ...
      </context>

The corpus is loaded and embedded once at application startup (see main.py lifespan).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class DocumentMeta:
    title: str
    url: str
    category: str
    scraped_by: str = ""
    scraped_date: str = ""
    team: str = ""


@dataclass
class Document:
    meta: DocumentMeta
    content: str       # body text (front-matter stripped)
    file_path: str     # basename of the source .md file


@dataclass
class ScoredDocument:
    doc: Document
    score: float


# ---------------------------------------------------------------------------
# In-memory state (populated at startup)
# ---------------------------------------------------------------------------

_corpus: list[Document] = []
_embeddings: Optional[np.ndarray] = None   # shape: (n_docs, embed_dim)
_model: Optional[SentenceTransformer] = None

# All subdirectories we index — covers every category in the team's KB spec
_SUBDIRS = [
    "student_services",
    "academics",
    "faculty",
    "events",
    "policies",
    "placements",
    "research",
    "administration",
    "admissions",
    "achievements",
    "announcements",
    "careers",
    "cep",
    "governance",
    "infrastructure",
    "intranet",
    "news_articles",
    "notices",
    "people",
]

# Regex to strip the YAML front-matter block (--- ... ---)
_FRONT_MATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def _parse_front_matter(raw: str) -> tuple[DocumentMeta, str]:
    """
    Extract YAML front-matter fields into DocumentMeta and return the body.
    Uses simple line-by-line parsing to avoid a PyYAML dependency.
    """
    meta = DocumentMeta(title="", url="", category="")
    body = raw

    m = _FRONT_MATTER_RE.match(raw)
    if m:
        fm_block = m.group(1)
        body = raw[m.end():]
        for line in fm_block.splitlines():
            if ":" in line:
                key, _, val = line.partition(":")
                key = key.strip().lower()
                val = val.strip().strip('"').strip("'")
                if key == "title":
                    meta.title = val
                elif key == "url":
                    meta.url = val
                elif key == "category":
                    meta.category = val
                elif key == "scraped_by":
                    meta.scraped_by = val
                elif key == "scraped_date":
                    meta.scraped_date = val
                elif key == "team":
                    meta.team = val

    if not meta.title:
        # Fallback: derive title from filename (set by caller)
        pass

    return meta, body.strip()


def _filename_to_title(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").title()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_corpus() -> list[Document]:
    """
    Walk DATA_DIR for .md files in every recognised subdirectory.
    Content is capped at 2 000 chars per document.
    """
    data_dir = Path(settings.DATA_DIR)
    docs: list[Document] = []

    if not data_dir.exists():
        logger.warning("DATA_DIR does not exist: %s", data_dir)
        return docs

    for subdir_name in _SUBDIRS:
        subdir = data_dir / subdir_name
        if not subdir.is_dir():
            continue
        for md_file in sorted(subdir.rglob("*.md")):
            try:
                raw = md_file.read_text(encoding="utf-8", errors="replace")
                meta, body = _parse_front_matter(raw)

                # Fill in defaults for missing front-matter fields
                if not meta.title:
                    meta.title = _filename_to_title(md_file.name)
                if not meta.category:
                    meta.category = subdir_name.replace("_", " ").title()

                docs.append(
                    Document(
                        meta=meta,
                        content=body[:2000],
                        file_path=md_file.name,
                    )
                )
            except Exception as exc:  # pragma: no cover
                logger.error("Failed to load %s: %s", md_file, exc)

    logger.info("Loaded %d documents from %s", len(docs), data_dir)
    return docs


def build_index(corpus: list[Document]) -> None:
    """
    Encode all documents with sentence-transformers.
    Called once at application startup — stores normalised embeddings
    for fast cosine similarity via dot product.
    """
    global _corpus, _embeddings, _model

    _corpus = corpus
    if not corpus:
        logger.warning("Corpus is empty — RAG index will not be built.")
        return

    logger.info("Loading embedding model: %s", settings.EMBED_MODEL)
    _model = SentenceTransformer(settings.EMBED_MODEL)

    texts = [f"{doc.meta.title}\n{doc.meta.category}\n{doc.content}" for doc in corpus]
    logger.info("Encoding %d documents…", len(texts))
    embs: np.ndarray = _model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    # L2-normalise for cosine similarity via dot product
    norms = np.linalg.norm(embs, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    _embeddings = embs / norms

    logger.info("Index built — shape: %s", _embeddings.shape)


def retrieve(query: str) -> list[ScoredDocument]:
    """
    Encode the query and return the top-K most similar documents.
    Returns an empty list if the index is not ready yet.
    """
    if _model is None or _embeddings is None or not _corpus:
        logger.warning("RAG index not ready — returning empty results.")
        return []

    q_vec: np.ndarray = _model.encode([query], convert_to_numpy=True)
    norm = float(np.linalg.norm(q_vec))
    if norm > 0:
        q_vec = q_vec / norm

    scores: np.ndarray = (_embeddings @ q_vec.T).flatten()
    top_idx = np.argsort(scores)[::-1][: settings.TOP_K]

    return [
        ScoredDocument(doc=_corpus[i], score=float(scores[i]))
        for i in top_idx
        if scores[i] > 0.0
    ]


def build_context_xml(scored_docs: list[ScoredDocument]) -> str:
    """
    Render retrieved documents in the <context><doc ...> format expected
    by the team's system_prompt_v1.md.
    """
    if not scored_docs:
        return ""

    parts = ["<context>"]
    for i, sd in enumerate(scored_docs, 1):
        doc = sd.doc
        parts.append(
            f'<doc id="{i}" title="{doc.meta.title}" '
            f'category="{doc.meta.category}" '
            f'url="{doc.meta.url}">'
            f"\n{doc.content}\n</doc>"
        )
    parts.append("</context>")
    return "\n".join(parts)
