"""
test_document_aware_chunking.py — Unit Tests for Strategy-Based Document-Aware Chunking Architecture
"""

from __future__ import annotations
import unittest
from pathlib import Path
from strategies import (
    ChunkingStrategyRegistry,
    TokenChunkStrategy,
    ClubChunkStrategy,
    FacultyChunkStrategy,
    CourseChunkStrategy,
    FAQChunkStrategy,
    ContactDirectoryChunkStrategy
)


class TestDocumentAwareChunking(unittest.TestCase):

    def test_club_chunk_strategy_prevents_entity_mixing(self):
        """Verify ClubChunkStrategy isolates individual clubs/committees into distinct single-entity chunks."""
        text = """
## Dance Club (DADC)
Convener: Rahul Sharma
Deputy: Priya Patel
Faculty Mentor: Prof. Anil Roy

## Synapse Committee
Convener: Amit Shah
Deputy: Sneha Gupta
Faculty Mentor: Prof. Meera Joshi
"""
        meta = {"category": "student_committees", "title": "C_DCs Information 2024-25"}
        file_path = "data/governance/c_dcs_2024.md"

        strategy = ClubChunkStrategy()
        self.assertTrue(strategy.can_handle(text, meta, file_path))

        chunks = strategy.chunk(text, meta, file_path)
        self.assertEqual(len(chunks), 2)
        self.assertIn("Dance Club", chunks[0])
        self.assertNotIn("Synapse Committee", chunks[0])
        self.assertIn("Synapse Committee", chunks[1])
        self.assertNotIn("Dance Club", chunks[1])

    def test_faculty_chunk_strategy(self):
        """Verify FacultyChunkStrategy isolates faculty members into individual chunks."""
        text = """
## Prof. Anish Mathur
Designation: Professor
Department: Computer Science
Research Interests: Artificial Intelligence, Machine Learning

## Dr. Sunita Rao
Designation: Associate Professor
Department: Mathematics
Research Interests: Applied Algebra, Cryptography
"""
        meta = {"category": "faculty", "title": "Faculty Directory"}
        file_path = "data/faculty/directory.md"

        strategy = FacultyChunkStrategy()
        self.assertTrue(strategy.can_handle(text, meta, file_path))

        chunks = strategy.chunk(text, meta, file_path)
        self.assertEqual(len(chunks), 2)
        self.assertIn("Prof. Anish Mathur", chunks[0])
        self.assertNotIn("Dr. Sunita Rao", chunks[0])

    def test_faq_chunk_strategy(self):
        """Verify FAQChunkStrategy isolates Question-Answer pairs into individual chunks."""
        text = """
Q: How do I apply for hostel accommodation?
A: You can apply online through the student portal during the semester registration window.

Q: What is the last date for fee payment?
A: The deadline for autumn semester fee payment is August 10.
"""
        meta = {"category": "admissions", "title": "Hostel Admissions FAQ"}
        file_path = "data/academics/faq.md"

        strategy = FAQChunkStrategy()
        self.assertTrue(strategy.can_handle(text, meta, file_path))

        chunks = strategy.chunk(text, meta, file_path)
        self.assertEqual(len(chunks), 2)
        self.assertIn("How do I apply", chunks[0])
        self.assertNotIn("last date for fee payment", chunks[0])

    def test_registry_fallback_to_token_chunk_strategy(self):
        """Verify registry falls back to TokenChunkStrategy for narrative prose policies."""
        text = "This is a general narrative university policy. " * 50
        meta = {"category": "policies", "title": "General Conduct Code"}
        file_path = "data/governance/conduct_code.md"

        chunks = ChunkingStrategyRegistry.chunk_section(text, meta, file_path)
        self.assertTrue(len(chunks) >= 1)
        self.assertIn("general narrative university policy", chunks[0])


if __name__ == "__main__":
    unittest.main()
