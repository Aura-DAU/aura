import os
import logging
import tempfile
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from rag import AURA
from pipeline.speech import transcribe_audio

# Ensure api runtime logging inherits standard visibility structures
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="API for RAG System - AURA")
aura = AURA()

speech_queue_lock = asyncio.Semaphore(1)

ALLOWED_FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

# Production CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
            # FIX: Assign the trackable path path immediately on resource allocation
            temp_path = temp_file.name
            
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_AUDIO_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Audio file exceeds {MAX_AUDIO_BYTES // (1024 * 1024)} MB limit"
                    )
                temp_file.write(chunk)

        # ADD THE ASYNC WITH CONTEXT AND INDENT THE EXECUTION
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
        logger.error("Request failed during processing", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # The cleanup hook is now completely guaranteed to wipe the file if it exists
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as cleanup_error:
                logger.error(f"Failed to remove temp file at {temp_path}: {cleanup_error}")