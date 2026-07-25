"""ChatRequest validation mirrors frontend Zod caps."""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from api.schemas import ChatRequest


def test_question_max_length_2000():
    ChatRequest(question="ok")
    with pytest.raises(ValidationError):
        ChatRequest(question="x" * 2001)


def test_history_max_turns_and_content():
    ok_history = [{"role": "user", "content": "hi"} for _ in range(20)]
    ChatRequest(question="q", history=ok_history)
    with pytest.raises(ValidationError):
        ChatRequest(
            question="q",
            history=[{"role": "user", "content": "hi"} for _ in range(21)],
        )
    with pytest.raises(ValidationError):
        ChatRequest(
            question="q",
            history=[{"role": "user", "content": "y" * 20_001}],
        )
