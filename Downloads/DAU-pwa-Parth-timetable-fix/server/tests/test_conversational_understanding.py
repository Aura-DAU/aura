import unittest
import sys
import os

# Add server and server/rag to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../rag")))

from personal_query_classifier import PersonalQueryClassifier, is_pure_profile_query
from pipeline.guardrails.query_guardrail import QueryGuardrail, Verdict, IMPLICIT_DAU_PAT
from pipeline.guardrails.wellness_guardrail import WellnessGuardrail
from pipeline.retrieval.query_planner import QueryPlanner, resolve_continuation_query, rewrite_personalized_academic_query
from pipeline.aura_chat import AuraChat, SimpleIdentity, is_greeting_or_meta


class TestConversationalUnderstanding(unittest.TestCase):

    def setUp(self):
        self.classifier = PersonalQueryClassifier()
        self.guardrail = QueryGuardrail()
        self.wellness = WellnessGuardrail()
        self.planner = QueryPlanner()
        self.mock_identity = SimpleIdentity({
            "erp_id": "202401001",
            "role": "student",
            "full_name": "Aarav Sharma",
            "roll_number": "202401001",
            "program": "B.Tech. (ICT)",
            "branch": "ICT",
            "current_sem": 5,
            "email": "202401001@dau.ac.in"
        })

    # 1. Implicit DAU Queries Test
    def test_implicit_dau_queries(self):
        implicit_queries = [
            "What clubs are here?",
            "What events are happening?",
            "Where is the canteen?",
            "What facilities are available?",
            "What hostel rules exist?",
            "Where is the library?",
            "What buses are available?",
            "What courses are offered?"
        ]
        for q in implicit_queries:
            with self.subTest(query=q):
                self.assertTrue(bool(IMPLICIT_DAU_PAT.search(q)), f"Query '{q}' should match IMPLICIT_DAU_PAT")
                is_safe = self.guardrail.is_safe(q)
                self.assertTrue(is_safe, f"Query '{q}' should be classified as SAFE")

    # 2. Pure Profile Queries Test (Fast-path <1ms, bypasses RAG & Wellness)
    def test_pure_profile_queries(self):
        profile_queries = [
            "Who am I?",
            "What is my name?",
            "What course am I enrolled in?",
            "Which branch am I in?",
            "What semester am I currently in?",
            "What is my roll number?",
            "What is my email?"
        ]
        for q in profile_queries:
            with self.subTest(query=q):
                self.assertTrue(is_pure_profile_query(q), f"Query '{q}' should be identified as pure profile query")
                res = self.classifier.classify(q)
                self.assertEqual(res["type"], "PERSONAL")
                self.assertEqual(res["intent"], "PROFILE")

    # 3. Conversation Continuation Test
    def test_conversation_continuation(self):
        history = [
            {"role": "user", "content": "Tell me about DAU clubs."},
            {"role": "assistant", "content": "DAU has over 20 active student clubs."}
        ]
        followup = "Which one is the biggest?"
        resolved = resolve_continuation_query(followup, history)
        self.assertIn("Tell me about DAU clubs.", resolved)
        self.assertIn("Which one is the biggest?", resolved)

    # 4. Greetings Test
    def test_greetings_fast_path(self):
        greetings = [
            "Hi", "Hello", "Good morning", "Good afternoon", "Good evening",
            "How are you?", "Have a nice day", "Thank you", "Bye", "See you", "Good night"
        ]
        for g in greetings:
            with self.subTest(greeting=g):
                self.assertTrue(is_greeting_or_meta(g), f"Greeting '{g}' should be identified as greeting/meta")

    # 5. Personalized Academic Queries Rewriting Test
    def test_personalized_academic_queries_rewriting(self):
        user_query = "What is the credit structure of my program?"
        rewritten = rewrite_personalized_academic_query(user_query, identity=self.mock_identity)
        self.assertIn("ICT", rewritten)
        self.assertIn("Dhirubhai Ambani University", rewritten)

    # 6. Program-Based Query Rewriting Test
    def test_program_based_query_rewriting(self):
        user_query = "What electives can I take?"
        # Simulate query planner plan()
        effective = rewrite_personalized_academic_query(user_query, identity=self.mock_identity)
        self.assertIsNotNone(effective)

    # 7. Wellness False Positives Exclusion Test
    def test_wellness_false_positives_exclusion(self):
        safe_queries = [
            "Who am I?",
            "Which course am I enrolled in?",
            "What branch am I studying?",
            "What subjects do I have?"
        ]
        for q in safe_queries:
            with self.subTest(query=q):
                is_distress = self.wellness.check(q)
                self.assertFalse(is_distress, f"Query '{q}' should NOT trigger wellness distress block")


if __name__ == "__main__":
    unittest.main()
