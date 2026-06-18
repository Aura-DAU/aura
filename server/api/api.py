import os
import sys
import tempfile
import asyncio
from typing import List, Optional
from pathlib import Path

# Add the server and server/rag directories to sys.path to resolve imports cleanly
server_dir = Path(__file__).resolve().parent.parent
rag_dir = server_dir / "rag"

if str(server_dir) not in sys.path:
    sys.path.insert(0, str(server_dir))
if str(rag_dir) not in sys.path:
    sys.path.insert(0, str(rag_dir))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from rag import AURA
from pipeline.speech import transcribe_audio

app = FastAPI(title="API for RAG System - AURA")
aura = AURA()

# ---------------------------------------------------------------------------
# CORS CONFIGURATION
# ---------------------------------------------------------------------------
# TODO: Extend ALLOWED_FRONTEND_ORIGINS with the prod frontend origin before deploy.
ALLOWED_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

prod_origin = os.getenv("PROD_FRONTEND_ORIGIN")

if prod_origin:
    ALLOWED_FRONTEND_ORIGINS.append(prod_origin)
    print(f"CORS: Enabled production origin: {prod_origin}")
else:
    print("CORS: Warning - PROD_FRONTEND_ORIGIN not set. Only localhost allowed.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# ARCHITECTURAL SAFEGUARD: SINGLE-FLIGHT WHISPER EXECUTION
# We intentionally use a Semaphore of 1 to serialize speech requests globally.
# Whisper is a highly CPU-bound machine learning task. Allowing concurrent 
# executions on standard hardware divides CPU attention, degrades throughput 
# exponentially, and risks OOM (Out-Of-Memory) application crashes.
# Students will queue asynchronously with near-zero overhead until the lock frees.
# Do not bump this value unless migrating to a dedicated GPU cluster.
# ---------------------------------------------------------------------------
speech_queue_lock = asyncio.Semaphore(1)

ffmpeg_env_path = os.getenv("FFMPEG_BINARY_PATH")

if ffmpeg_env_path and os.path.exists(ffmpeg_env_path):
    if ffmpeg_env_path not in os.environ["PATH"]:
        os.environ["PATH"] += os.pathsep + ffmpeg_env_path

UNIVERSITY_PROMPT = "DAIICT, Prof. Hemant A. Patil, Placement Convener, B.Tech, M.Tech, ICT, Gandhinagar."

class HistoryTurn(BaseModel):
    role: str
    content: str

class StudentProfile(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    year: Optional[str] = None
    semester: Optional[str] = None
    interests: Optional[str] = None

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[HistoryTurn]] = None
    studentProfile: Optional[StudentProfile] = None

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024

@app.post("/chat")
def chat(request: ChatRequest):
    history = (
        [turn.model_dump() for turn in request.history]
        if request.history
        else []
    )
    profile = (
        request.studentProfile.model_dump(exclude_none=True)
        if request.studentProfile
        else None
    )
    return aura.ask(question=request.question, history=history, profile=profile)


@app.post("/speech")
async def speech(file: UploadFile = File(...)):
    temp_path = None
    try:
        if not file.filename:
            raise HTTPException(
                status_code=400,
                detail="No filename provided"
            )
        
        extension = os.path.splitext(file.filename)[1].lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {extension}"
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_AUDIO_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Audio file exceeds {MAX_AUDIO_BYTES // (1024 * 1024)} MB limit"
                    )
                temp_file.write(chunk)

            temp_path = temp_file.name

        async with speech_queue_lock:
            question = await run_in_threadpool(
                transcribe_audio, 
                temp_path, 
                initial_prompt=UNIVERSITY_PROMPT
            )

        return {"text": question}

    except HTTPException:
        raise
    except Exception as e:
        print("Speech processing Error")
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/health")
async def health():
    return {
        "status": "online",
        "cors_origins": ALLOWED_FRONTEND_ORIGINS,
        "env_check": "PROD_FRONTEND_ORIGIN is " + ("SET" if os.getenv("PROD_FRONTEND_ORIGIN") else "MISSING")
    }