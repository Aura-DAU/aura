# Shared request/response models for AURA API routes.
from typing import Annotated, List, Optional

from pydantic import BaseModel, Field

UNIVERSITY_PROMPT = (
    "Dhirubhai Ambani University, DAU, DA-IICT, Gandhinagar. "
    "B.Tech ICT, B.Tech CS AI, B.Tech ECE, BS-MS, M.Tech, M.Sc, M.Des, Ph.D. "
    "AURA, CGPA, semester, admissions, fees, hostel, scholarship, placement."
)

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
    userProfile: Optional[UserProfile] = None
    studentProfile: Optional[UserProfile] = None

    def resolved_profile(self) -> Optional[UserProfile]:
        return self.studentProfile or self.userProfile


class LinkEcampusRequest(BaseModel):
    ecampus_username: str = Field(..., min_length=1, max_length=200)
    ecampus_password: str = Field(..., min_length=1, max_length=500)
