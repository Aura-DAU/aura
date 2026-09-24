import sys
import unittest
from pathlib import Path

INGESTION_DIR = Path(__file__).resolve().parent.parent / "rag" / "pipeline" / "ingestion" / "chunking"
sys.path.insert(0, str(INGESTION_DIR))

from chunker import split_section  # noqa: E402
from process_corpus import (  # noqa: E402
    _EMBED_TOKEN_LIMIT,
    _adaptive_split_entity,
    _embed_token_len,
    extract_faculty_from_text,
)


class TestChunkTextPreservation(unittest.TestCase):

    def test_token_split_keeps_original_case_and_numbers(self):
        text = "Tuition Fee for B.Tech. (ICT) is Rs. 1,85,000 per semester. " * 40
        chunks = split_section(text)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertIn(chunk, text)
        self.assertIn("B.Tech. (ICT) is Rs. 1,85,000", chunks[0])

    def test_adaptive_split_respects_embedding_limit(self):
        row = "| " + " | ".join(f"https://daiict.ac.in/page/{i}/x" for i in range(60)) + " |"
        chunks = _adaptive_split_entity(row, max_tokens=256)
        self.assertTrue(all(_embed_token_len(c) <= _EMBED_TOKEN_LIMIT + 30 for c in chunks))

    def test_advisor_names_are_not_split_inside_words(self):
        names = extract_faculty_from_text("Advisors: Prof. Zzanandq Kumar and Dr. Qqchandranx")
        self.assertNotIn("Zz", names)
        self.assertNotIn("Qqch", names)
        self.assertTrue(any("Zzanandq" in n for n in names))


if __name__ == "__main__":
    unittest.main()
