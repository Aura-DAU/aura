# Shared request/response models for AURA API routes.
from typing import List, Optional

from pydantic import BaseModel

UNIVERSITY_PROMPT = (
    "Dhirubhai Ambani University, DAU, DA-IICT, Gandhinagar. "
    "B.Tech ICT, B.Tech CS AI, B.Tech ECE, BS-MS, M.Tech, M.Sc, M.Des, Ph.D. "
    "AURA, CGPA, semester, admissions, fees, hostel, scholarship, placement."
)

ALLOWED_AUDIO = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024


class HistoryTurn(BaseModel):
    role: str
    content: str


class UserProfile(BaseModel):
    # Display only — role/identity come from JWT via require_identity().
    name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[str] = None
    semester: Optional[str] = None
    interests: Optional[str] = None
    subjects: Optional[List[str]] = None


class ChatRequest(BaseModel):
    question: str
    history: Optional[List[HistoryTurn]] = None
    userProfile: Optional[UserProfile] = None
    studentProfile: Optional[UserProfile] = None

    def resolved_profile(self) -> Optional[UserProfile]:
        return self.studentProfile or self.userProfile


class LinkEcampusRequest(BaseModel):
    ecampus_username: str
    ecampus_password: str
