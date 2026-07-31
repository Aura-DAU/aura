import unittest
import uuid
import sys
from pathlib import Path

# Ensure ingestion modules are in Python path
INGESTION_DIR = Path(__file__).resolve().parent.parent / "rag" / "pipeline" / "ingestion" / "chunking"
sys.path.insert(0, str(INGESTION_DIR))

from chunk_id_generator import (
    generate_deterministic_chunk_id,
    normalize_relative_path,
    normalize_text_for_hashing,
    AURA_CHUNK_NAMESPACE
)


class TestDeterministicChunkIDs(unittest.TestCase):

    def setUp(self):
        self.sample_path = "data/academics/course_policy.md"
        self.sample_text_1 = "This course covers Distributed Systems and Database Internals."
        self.sample_text_2 = "Grading policy: Midsem 30%, Endsem 50%, Assignments 20%."

    def test_same_file_ingested_twice_produces_identical_ids(self):
        """Case 1: Same file, same content -> Identical chunk IDs."""
        id1 = generate_deterministic_chunk_id(self.sample_path, self.sample_text_1, section_key="Overview")
        id2 = generate_deterministic_chunk_id(self.sample_path, self.sample_text_1, section_key="Overview")
        
        self.assertEqual(id1, id2)
        # Verify valid UUIDv5 format
        parsed = uuid.UUID(id1)
        self.assertEqual(parsed.version, 5)

    def test_one_section_changed_only_affected_chunk_id_changes(self):
        """Case 2: Changing text in section 2 changes only section 2's ID, leaving section 1 unchanged."""
        sec1_id_orig = generate_deterministic_chunk_id(self.sample_path, self.sample_text_1, section_key="Overview")
        sec2_id_orig = generate_deterministic_chunk_id(self.sample_path, self.sample_text_2, section_key="Grading")

        # Modify section 2 text
        modified_text_2 = "Grading policy: Midsem 40%, Endsem 40%, Assignments 20%."
        sec2_id_new = generate_deterministic_chunk_id(self.sample_path, modified_text_2, section_key="Grading")

        # Section 1 ID MUST remain completely identical
        sec1_id_after = generate_deterministic_chunk_id(self.sample_path, self.sample_text_1, section_key="Overview")
        
        self.assertEqual(sec1_id_orig, sec1_id_after)
        self.assertNotEqual(sec2_id_orig, sec2_id_new)

    def test_different_file_paths_with_identical_content_produce_distinct_ids(self):
        """Case 3: Same text in different files gets path-isolated unique IDs."""
        path_a = "data/academics/autumn/cs101.md"
        path_b = "data/academics/winter/cs101.md"
        
        id_a = generate_deterministic_chunk_id(path_a, self.sample_text_1)
        id_b = generate_deterministic_chunk_id(path_b, self.sample_text_1)

        self.assertNotEqual(id_a, id_b)

    def test_whitespace_normalization_preserves_id_stability(self):
        """Whitespace variations (e.g. CRLF vs LF or trailing spaces) do not invalidate IDs."""
        text_lf = "Line 1\nLine 2  \nLine 3"
        text_crlf = "Line 1\r\nLine 2\r\nLine 3"

        id_lf = generate_deterministic_chunk_id(self.sample_path, text_lf)
        id_crlf = generate_deterministic_chunk_id(self.sample_path, text_crlf)

        self.assertEqual(id_lf, id_crlf)

    def test_path_normalization(self):
        """Path separators and capitalization normalization."""
        raw_path = "DATA\\Academics\\Course_Policy.md"
        norm = normalize_relative_path(raw_path)
        self.assertEqual(norm, "data/academics/course_policy.md")


if __name__ == "__main__":
    unittest.main()
