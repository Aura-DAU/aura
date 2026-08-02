# Shared request/response models for AURA API routes.
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field, SecretStr

ALLOWED_AUDIO = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024


class HistoryTurn(BaseModel):
    role: str = Field(..., max_length=32)
    content: str = Field(..., max_length=20_000)


class UserProfile(BaseModel):
    # Display only — role/identity come from JWT via require_identity().
    name: Optional[str] = Field(None, max_length=200)
    branch: Optional[str] = Field(None, max_length=200)
    year: Optional[str] = Field(None, max_length=50)
    semester: Optional[str] = Field(None, max_length=50)
    interests: Optional[str] = Field(None, max_length=1000)
    subjects: Optional[List[Annotated[str, Field(max_length=100)]]] = Field(None, max_length=50)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    history: Optional[List[HistoryTurn]] = Field(None, max_length=20)
    # Client-owned rolling conversation memory (pipeline.memory). The server is
    # stateless: the client sends this digest plus the unsummarised tail each
    # turn and gets an updated digest back to persist.
    summary: Optional[str] = Field(None, max_length=20_000)
    # Stable per-conversation id (client-owned thread id). Keys this chat's block
    # in the persistent per-user memory so every conversation — even a short one
    # that never compacts — is captured and updated in place across turns.
    threadId: Optional[str] = Field(None, max_length=64)
    userProfile: Optional[UserProfile] = None
    studentProfile: Optional[UserProfile] = None

    def resolved_profile(self) -> Optional[UserProfile]:
        return self.studentProfile or self.userProfile


class LinkEcampusRequest(BaseModel):
    ecampus_username: str = Field(..., min_length=1, max_length=200)
    # SEC-03 fix: SecretStr instead of str. pydantic's repr/str/logging never
    # exposes the raw value (renders as `SecretStr('**********')`), so an
    # exception or log line captured between this schema and the point of
    # encryption can't leak the password. get_secret_value() is called only
    # at the moment of encryption, in credentials_vault.store_credentials.
    ecampus_password: SecretStr = Field(..., min_length=1, max_length=500)
