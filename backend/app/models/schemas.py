from pydantic import BaseModel, field_validator
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Shared message type used by both request history and internal tracking
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


# ---------------------------------------------------------------------------
# Student profile — sent by the PWA frontend for response personalisation.
# All fields are optional so the schema stays backward-compatible with callers
# that do not include profile data.
# ---------------------------------------------------------------------------

class StudentProfile(BaseModel):
    name: str = ""
    branch: str = ""
    year: str = ""
    semester: str = ""
    interests: str = ""


# ---------------------------------------------------------------------------
# /api/chat  —  Request
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    # Optional: PWA sends studentProfile; ignored if not provided
    student_profile: Optional[StudentProfile] = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("message must not be empty")
        return v


# ---------------------------------------------------------------------------
# /api/chat  —  Response (superset)
#
# Satisfies two contracts simultaneously:
#   1. Eval harness (run_eval.py):  reads `answer` and `sources`
#   2. PWA frontend (useAuraChat):  reads `success`, `content`, `citations`
#
# The Next.js proxy at pwa/src/app/api/chat/route.ts forwards this verbatim.
# ---------------------------------------------------------------------------

class PwaCitation(BaseModel):
    title: str
    file: str


class ChatResponse(BaseModel):
    # Eval-harness fields
    answer: str
    sources: list[str] = []     # source URLs from document YAML front-matter

    # PWA frontend fields (mirrors PwaChatResponse shape)
    success: bool = True
    content: str = ""           # same text as `answer`; populated by endpoint
    citations: list[PwaCitation] = []


# ---------------------------------------------------------------------------
# Legacy /api/chat/pwa bridge — kept for backward compatibility.
# New callers should prefer /api/chat which now returns the superset above.
# ---------------------------------------------------------------------------

class PwaChatResponse(BaseModel):
    success: bool
    content: str
    citations: list[PwaCitation] = []
