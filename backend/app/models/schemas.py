from pydantic import BaseModel, field_validator
from typing import Literal


# ---------------------------------------------------------------------------
# Shared message type used by both request history and internal tracking
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


# ---------------------------------------------------------------------------
# /api/chat  —  Request
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v


# ---------------------------------------------------------------------------
# /api/chat  —  Response
#
# Matches the contract expected by the eval harness (run_eval.py):
#   { "answer": "...", "sources": ["url1", "url2"] }
#
# The Next.js ragClient.ts also reads these fields.
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []     # source URLs from document YAML front-matter


# ---------------------------------------------------------------------------
# Legacy / PWA bridge — the Next.js frontend currently expects the shape:
#   { success, content, citations: [{title, file}] }
# We expose this as an additional response model for the /api/chat/pwa route.
# ---------------------------------------------------------------------------

class PwaCitation(BaseModel):
    title: str
    file: str


class PwaChatResponse(BaseModel):
    success: bool
    content: str
    citations: list[PwaCitation] = []
