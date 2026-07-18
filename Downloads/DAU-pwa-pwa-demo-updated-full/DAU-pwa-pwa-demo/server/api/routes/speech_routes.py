"""
Speech route — POST /speech

Extracted from api.py to keep routes modular and under 300 lines per CLAUDE.md.
Uses a semaphore to limit concurrent Whisper inference (GPU/CPU contention).
"""
import asyncio
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from api.auth import require_identity, Identity
from pipeline.speech import transcribe_audio

router = APIRouter()

# Serialize Whisper inference — one request at a time to avoid OOM on shared GPU.
_speech_queue_lock = asyncio.Semaphore(1)

# Inject a bundled ffmpeg binary path if one is provided via env (Docker image
# may ship ffmpeg at a non-PATH location).
_ffmpeg_path = os.getenv("FFMPEG_BINARY_PATH")
if _ffmpeg_path and os.path.exists(_ffmpeg_path):
    if _ffmpeg_path not in os.environ.get("PATH", ""):
        os.environ["PATH"] += os.pathsep + _ffmpeg_path

ALLOWED_AUDIO   = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024  # 25 MB — matches nginx client_max_body_size

# DAU-specific Whisper initial_prompt to improve transcription accuracy for
# university terminology (programme names, CGPA, etc.).
_UNIVERSITY_PROMPT = (
    "Dhirubhai Ambani University, DAU, DA-IICT, Gandhinagar. "
    "B.Tech ICT, B.Tech CS AI, B.Tech ECE, BS-MS, M.Tech, M.Sc, M.Des, Ph.D. "
    "AURA, CGPA, semester, admissions, fees, hostel, scholarship, placement."
)


@router.post("/speech")
async def speech(
    file:     UploadFile = File(...),
    identity: Identity   = Depends(require_identity),
):
    temp_path = None
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_AUDIO:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            size = 0
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_AUDIO_BYTES:
                    raise HTTPException(status_code=413, detail="Audio file too large")
                tmp.write(chunk)
            temp_path = tmp.name

        async with _speech_queue_lock:
            question = await run_in_threadpool(
                transcribe_audio, temp_path, initial_prompt=_UNIVERSITY_PROMPT
            )
        return {"text": question}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
