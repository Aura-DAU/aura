"""
chunk_id_generator.py — Production-grade Deterministic Chunk ID Generator for AURA RAG

Generates stable, machine-independent, collision-resistant UUIDv5 chunk identifiers
derived from canonical file paths, section headings, and content hashes.

Satisfies Qdrant Point ID requirements (UUIDv5 format).
"""

import uuid
import hashlib
import re
from typing import Optional

# Fixed Namespace UUID for AURA Document Chunks (Derived from AURA URL namespace)
AURA_CHUNK_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://aura.daiict.ac.in/chunks")


def normalize_text_for_hashing(text: str) -> str:
    """
    Normalizes text for deterministic hashing:
    - Replaces CRLF with LF
    - Strips leading/trailing whitespace
    - Collapses repetitive inline whitespace while preserving line structure
    """
    if not text:
        return ""
    text_clean = text.replace("\r\n", "\n").strip()
    # Normalize multiple spaces per line & strip trailing line whitespace
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text_clean.split("\n")]
    return "\n".join(lines)


def normalize_relative_path(file_path: str) -> str:
    """
    Converts a file path or relative path into a canonical, OS-independent string.
    e.g., 'data/academics/course_policy.md'
    """
    if not file_path:
        return "data/unknown.md"
    
    path_str = str(file_path).replace("\\", "/").lower()
    if "data/" in path_str:
        path_str = "data/" + path_str.split("data/", 1)[1]
    
    return path_str.strip("/")


def generate_deterministic_chunk_id(
    relative_path: str,
    chunk_text: str,
    section_key: Optional[str] = None,
    chunk_index: Optional[int] = None
) -> str:
    """
    Generates a deterministic UUIDv5 chunk ID.
    
    Formula:
      canonical_path = normalize_relative_path(relative_path)
      content_hash = sha256(normalize_text(chunk_text))[:16]
      key_string = f"{canonical_path}::{section_key or ''}::{content_hash}"
      chunk_id = uuid.uuid5(AURA_CHUNK_NAMESPACE, key_string)

    Properties:
    - Deterministic: Same document & content -> Exact same UUIDv5 across machines & runs.
    - Content-Aware: Localized paragraph edits only change the ID of affected chunks.
    - Path-Isolated: Identical chunk text in different files gets unique UUIDs.
    - Qdrant Compatible: Valid UUID string.
    """
    canonical_path = normalize_relative_path(relative_path)
    normalized_text = normalize_text_for_hashing(chunk_text)
    
    # 16-char SHA-256 digest of normalized text
    text_hash = hashlib.sha256(normalized_text.encode("utf-8")).hexdigest()[:16]
    
    sec_part = (section_key or "").strip().lower()
    key_str = f"{canonical_path}::{sec_part}::{text_hash}"
    
    return str(uuid.uuid5(AURA_CHUNK_NAMESPACE, key_str))
