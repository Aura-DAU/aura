from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
import tempfile
from pydantic import BaseModel
from rag import AURA
from pipeline.speech import transcribe_audio
import os
from typing import List, Optional

app = FastAPI(title="API for RAG System - AURA")
aura = AURA()

FFMPEG_DIR = r"C:\Users\pushk\Downloads\ffmpeg-2026-06-10-git-b29bdd3715-essentials_build\ffmpeg-2026-06-10-git-b29bdd3715-essentials_build\bin"
if FFMPEG_DIR not in os.environ["PATH"]:
    os.environ["PATH"] += os.pathsep + FFMPEG_DIR

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
        [turn.model_dump()
         for turn in request.history]
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