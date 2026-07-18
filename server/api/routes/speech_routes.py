# POST /speech — Whisper transcription (serialized).
import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from api.auth import Identity, require_identity
from api.deps import speech_queue_lock
from api.schemas import ALLOWED_AUDIO, MAX_AUDIO_BYTES, UNIVERSITY_PROMPT

router = APIRouter(tags=["speech"])


@router.post("/speech")
async def speech(
    file: UploadFile = File(...),
    identity: Identity = Depends(require_identity),
):
    # Defer whisper import until first /speech call.
    from pipeline.speech import transcribe_audio

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

        async with speech_queue_lock:
            question = await run_in_threadpool(
                transcribe_audio, temp_path, initial_prompt=UNIVERSITY_PROMPT
            )
        return {"text": question}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
