"""
test_token_budgeting.py — Unit Tests for RAG Token Budgeting and Context Limits
"""

import unittest
from unittest.mock import MagicMock, patch
try:
    from config.token_budget_config import (
        LLM_MAX_CONTEXT_LENGTH,
        LLM_RESERVED_OUTPUT_TOKENS,
        LLM_MAX_INPUT_BUDGET,
        LLM_MAX_SYSTEM_PROMPT_BUDGET,
        LLM_MAX_CONTEXT_BUDGET,
        calculate_available_context_budget
    )
except ImportError:
    from token_budget_config import (
        LLM_MAX_CONTEXT_LENGTH,
        LLM_RESERVED_OUTPUT_TOKENS,
        LLM_MAX_INPUT_BUDGET,
        LLM_MAX_SYSTEM_PROMPT_BUDGET,
        LLM_MAX_CONTEXT_BUDGET,
        calculate_available_context_budget
    )
from pipeline.generation.answer_generator import AnswerGenerator, SYSTEM_PROMPT, _approx_token_count
from pipeline.retrieval.context_builder import ContextBuilder


class TestTokenBudgeting(unittest.TestCase):

    def test_token_budget_configuration_defaults(self):
        """Verify token budget configuration defaults match specifications."""
        self.assertEqual(LLM_MAX_CONTEXT_LENGTH, 8192)
        self.assertEqual(LLM_RESERVED_OUTPUT_TOKENS, 1024)
        self.assertEqual(LLM_MAX_INPUT_BUDGET, 7168)
        self.assertEqual(LLM_MAX_SYSTEM_PROMPT_BUDGET, 1800)
        self.assertEqual(LLM_MAX_CONTEXT_BUDGET, 4000)

    def test_system_prompt_token_count(self):
        """Verify refactored SYSTEM_PROMPT is compact (< 800 tokens)."""
        prompt_tokens = _approx_token_count(SYSTEM_PROMPT)
        self.assertLess(prompt_tokens, 800, f"System prompt token count ({prompt_tokens}) should be under 800 tokens")

    def test_calculate_available_context_budget(self):
        """Verify context budget calculation subtracts consumed system/user/history tokens."""
        # Sys=500, Hist=500, User=168 -> Consumed=1168 -> Available = 7168 - 1168 = 6000 (capped at MAX_CONTEXT_BUDGET=4000)
        avail = calculate_available_context_budget(500, 500, 168)
        self.assertEqual(avail, 4000)

        # Large consumption: Sys=1000, Hist=5000, User=1000 -> Consumed=7000 -> Available = 7168 - 7000 = 168
        avail_tight = calculate_available_context_budget(1000, 5000, 1000)
        self.assertEqual(avail_tight, 168)

    def test_context_builder_respects_token_budget(self):
        """Verify ContextBuilder caps chunks within token budget limits."""
        builder = ContextBuilder()
        large_chunks = [
            {
                "metadata": {
                    "text": "Academic policy details " * 200,
                    "title": f"Doc {i}",
                    "document_year": "2024-25"
                }
            }
            for i in range(15)
        ]
        res = builder.build(large_chunks)
        context_str = res["context"]
        estimated = builder._estimate_tokens(context_str)
        self.assertLessEqual(estimated, LLM_MAX_CONTEXT_BUDGET + 500)

    @patch("pipeline.generation.answer_generator.InferenceRouter.call_with_rotation")
    def test_generator_catches_400_bad_request_error(self, mock_rotation):
        """Verify AnswerGenerator catches 400 BadRequestError and returns structured message instead of failing."""
        mock_rotation.side_effect = Exception("400 BadRequestError: This model's maximum context length is 8192 tokens")
        gen = AnswerGenerator()
        response = gen.generate(
            query="What is the policy?",
            context="<context><doc id=\"1\">Policy info</doc></context>",
            plan={"retrieval_intent": "general"}
        )
        self.assertIn("exceeded the model's maximum context length limit", response)
        self.assertNotIn("500", response)


if __name__ == "__main__":
    unittest.main()
