"""
token_budget_config.py — Production Token Budgeting Configuration for AURA RAG

Centralized, environment-configurable token limits and budgets to guarantee that
no LLM request exceeds the model's maximum context window (e.g. 8192 tokens).
"""

import os

def _get_env_int(key: str, default: int) -> int:
    try:
        val = os.getenv(key, "").strip()
        return int(val) if val else default
    except (ValueError, TypeError):
        return default

# 1. Total Model Context Ceiling (e.g. 8192 for Qwen3-32B-AWQ / Groq / vLLM)
LLM_MAX_CONTEXT_LENGTH: int = _get_env_int("LLM_MAX_CONTEXT_LENGTH", 8192)

# 2. Reserved Output / Completion Tokens (e.g. 1024 tokens)
LLM_RESERVED_OUTPUT_TOKENS: int = _get_env_int("AURA_MAX_ANSWER_TOKENS", _get_env_int("LLM_RESERVED_OUTPUT_TOKENS", 1024))

# 3. Maximum Allowable Input Prompt Budget (Max Context - Reserved Output)
LLM_MAX_INPUT_BUDGET: int = LLM_MAX_CONTEXT_LENGTH - LLM_RESERVED_OUTPUT_TOKENS  # Default: 7168

# 4. Maximum System Prompt Budget (Target: < 1500 tokens)
LLM_MAX_SYSTEM_PROMPT_BUDGET: int = _get_env_int("LLM_MAX_SYSTEM_PROMPT_BUDGET", 1800)

# 5. Maximum Retrieved Context Budget (Target: < 4000 tokens)
LLM_MAX_CONTEXT_BUDGET: int = _get_env_int("LLM_MAX_CONTEXT_BUDGET", 4000)


def calculate_available_context_budget(system_tokens: int, history_tokens: int, user_tokens: int) -> int:
    """
    Calculates the exact token budget remaining for retrieved context chunks.
    """
    consumed = system_tokens + history_tokens + user_tokens
    available = LLM_MAX_INPUT_BUDGET - consumed
    return max(0, min(available, LLM_MAX_CONTEXT_BUDGET))
