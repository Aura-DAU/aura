"""
strategies.py — Document-Aware Strategy-Based Chunking Architecture for AURA.

Implements the Strategy + Registry pattern (ChunkingStrategyRegistry) for
document-aware chunking. Provides specialized entity-level chunking for
structured documents (Clubs, Faculty, Courses, FAQs, Contacts) and falls back
to TokenChunkStrategy for narrative prose (Policies, SOPs, Notices, Reports, Manuals).
"""

from abc import ABC, abstractmethod
import re
from typing import List, Dict, Any

from chunker import split_section


class BaseChunkingStrategy(ABC):
    """Abstract Base Class for all document-aware chunking strategies."""

    @abstractmethod
    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        """Determines whether this strategy should handle the given document section."""
        pass

    @abstractmethod
    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        """Generates a list of chunk strings from the input section text."""
        pass


class TokenChunkStrategy(BaseChunkingStrategy):
    """
    Default Narrative Strategy. Wraps the existing sentence-boundary snapped
    256-token chunker (CHUNK_SIZE=256, CHUNK_OVERLAP=40).
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        # Fallback strategy: handles narrative prose
        return True

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        return split_section(text)


class ClubChunkStrategy(BaseChunkingStrategy):
    """
    Structured Strategy for Club and Student Committee Directories.
    Extracts 1 club / committee record per chunk to prevent entity mixing.
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        cat = str(metadata.get("category") or "").lower()
        title = str(metadata.get("title") or "").lower()
        path = str(file_path).lower()
        text_lower = text.lower()

        is_club_meta = any(k in cat or k in title or k in path for k in ["club", "committee", "c_dcs", "sbg"])
        has_club_keys = ("convener" in text_lower or "deputy" in text_lower or "mentor" in text_lower)
        return is_club_meta or (has_club_keys and ("club" in text_lower or "committee" in text_lower))

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        # Split by entity headers (e.g. ## Club Name or ### Committee Name) or double-newline blocks
        blocks = re.split(r'\n(?=#{2,4}\s+)', text)
        if len(blocks) <= 1:
            blocks = re.split(r'\n{2,}(?=[A-Z0-9#])', text)

        chunks = []
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)
        return chunks if chunks else [text]


class FacultyChunkStrategy(BaseChunkingStrategy):
    """
    Structured Strategy for Faculty Directories.
    Extracts 1 faculty member profile per chunk.
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        cat = str(metadata.get("category") or "").lower()
        title = str(metadata.get("title") or "").lower()
        path = str(file_path).lower()
        text_lower = text.lower()

        is_faculty_meta = any(k in cat or k in title or k in path for k in ["faculty", "professor", "doctoral scholars"])
        has_faculty_keys = ("designation" in text_lower or "research interest" in text_lower or "office room" in text_lower)
        return is_faculty_meta or has_faculty_keys

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        blocks = re.split(r'\n(?=#{2,4}\s+)', text)
        if len(blocks) <= 1:
            blocks = re.split(r'\n{2,}(?=Faculty Name:|Name:|Dr\.|Prof\.)', text, flags=re.IGNORECASE)

        chunks = []
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)
        return chunks if chunks else [text]


class CourseChunkStrategy(BaseChunkingStrategy):
    """
    Structured Strategy for Course Catalogues and Syllabi.
    Extracts 1 course syllabus / description per chunk.
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        cat = str(metadata.get("category") or "").lower()
        title = str(metadata.get("title") or "").lower()
        path = str(file_path).lower()
        text_lower = text.lower()

        is_course_meta = any(k in cat or k in title or k in path for k in ["course", "curriculum", "syllabus", "catalogue"])
        has_course_keys = ("course code" in text_lower or "credits" in text_lower or "l-t-p-c" in text_lower)
        return is_course_meta or has_course_keys

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        blocks = re.split(r'\n(?=#{2,4}\s+)', text)
        if len(blocks) <= 1:
            blocks = re.split(r'\n{2,}(?=[A-Z]{2,4}\s*\d{3})', text)

        chunks = []
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)
        return chunks if chunks else [text]


class FAQChunkStrategy(BaseChunkingStrategy):
    """
    Structured Strategy for Frequently Asked Questions (FAQ).
    Extracts 1 Question-Answer pair per chunk.
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        cat = str(metadata.get("category") or "").lower()
        title = str(metadata.get("title") or "").lower()
        path = str(file_path).lower()
        text_lower = text.lower()

        is_faq_meta = "faq" in cat or "faq" in title or "faq" in path
        has_qa_patterns = bool(re.search(r'(?:^|\n)(?:Q:|Question:|###\s*Q)', text, re.IGNORECASE))
        return is_faq_meta or has_qa_patterns

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        blocks = re.split(r'\n(?=(?:Q:|Question:|###?\s*Q|\*\*Q:?\*\*))', text, flags=re.IGNORECASE)
        chunks = []
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)
        return chunks if chunks else [text]


class ContactDirectoryChunkStrategy(BaseChunkingStrategy):
    """
    Structured Strategy for Contact Directories and Emergency Numbers.
    Extracts 1 contact / desk entry per chunk.
    """

    def can_handle(self, text: str, metadata: dict, file_path: str) -> bool:
        cat = str(metadata.get("category") or "").lower()
        title = str(metadata.get("title") or "").lower()
        path = str(file_path).lower()
        text_lower = text.lower()

        is_contact_meta = any(k in cat or k in title or k in path for k in ["contact", "directory", "phone", "helpline", "emergency"])
        has_phone_keys = ("extension" in text_lower or "phone" in text_lower or "079-" in text_lower or "toll-free" in text_lower)
        return is_contact_meta or has_phone_keys

    def chunk(self, text: str, metadata: dict, file_path: str) -> List[str]:
        blocks = re.split(r'\n(?=#{2,4}\s+)', text)
        if len(blocks) <= 1:
            blocks = re.split(r'\n{2,}', text)

        chunks = []
        for block in blocks:
            cleaned = block.strip()
            if cleaned:
                chunks.append(cleaned)
        return chunks if chunks else [text]


class ChunkingStrategyRegistry:
    """
    Central Registry for Document-Aware Chunking Strategies.
    Iterates registered strategies in priority order, dispatching to the first matching strategy.
    """

    _strategies: List[BaseChunkingStrategy] = []
    _fallback_strategy: BaseChunkingStrategy = TokenChunkStrategy()

    @classmethod
    def register(cls, strategy: BaseChunkingStrategy) -> None:
        cls._strategies.append(strategy)

    @classmethod
    def chunk_section(cls, text: str, metadata: dict, file_path: str) -> List[str]:
        """
        Dispatches section chunking to the appropriate registered strategy.
        Falls back to TokenChunkStrategy if no specialized strategy matches.
        """
        for strategy in cls._strategies:
            if strategy.can_handle(text, metadata, file_path):
                return strategy.chunk(text, metadata, file_path)
        return cls._fallback_strategy.chunk(text, metadata, file_path)


# Register specialized strategies in priority order
ChunkingStrategyRegistry.register(ClubChunkStrategy())
ChunkingStrategyRegistry.register(FacultyChunkStrategy())
ChunkingStrategyRegistry.register(CourseChunkStrategy())
ChunkingStrategyRegistry.register(FAQChunkStrategy())
ChunkingStrategyRegistry.register(ContactDirectoryChunkStrategy())
