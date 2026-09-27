import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "rag" / "eval"))

from answer_quality import consistency, is_abstention, score_answer, token_f1  # noqa: E402


class TestAnswerQuality(unittest.TestCase):

    def test_correct_answer_needs_expected_numbers(self):
        expected = "19+3 credits (with Honours elective)"
        good = score_answer(expected, "Semester IV has 19+3 credits, including the Honours elective.")
        bad = score_answer(expected, "Semester IV has 21 credits including the Honours elective.")
        self.assertTrue(good["correct"])
        self.assertFalse(bad["correct"])
        self.assertFalse(bad["numbers_ok"])

    def test_indian_digit_grouping_matches(self):
        result = score_answer("Tuition fee is Rs. 1,85,000", "The tuition fee is Rs. 185000 per semester.")
        self.assertTrue(result["numbers_ok"])

    def test_not_found_rows_require_abstention(self):
        self.assertTrue(score_answer("NOT_FOUND", "I could not find that information in the available university data.")["correct"])
        self.assertFalse(score_answer("NOT_FOUND", "The MBBS fee is Rs. 5,00,000.")["correct"])

    def test_abstention_is_not_a_correct_answer(self):
        result = score_answer("Library opens at 9 AM", "I could not find that information. 9")
        self.assertTrue(is_abstention("I could not find that information."))
        self.assertFalse(result["correct"])

    def test_rows_without_expected_answer_are_unscored(self):
        self.assertIsNone(score_answer("", "anything")["correct"])

    def test_token_f1_and_consistency(self):
        self.assertEqual(token_f1("hostel fee", ""), 0.0)
        self.assertGreater(token_f1("the hostel fee is high", "hostel fee is high"), 0.9)
        self.assertEqual(consistency(["same answer", "same answer"]), 1.0)
        self.assertLess(consistency(["fee is 100", "deadline is monday"]), 0.5)


if __name__ == "__main__":
    unittest.main()
