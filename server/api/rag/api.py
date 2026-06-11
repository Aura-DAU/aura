from fastapi import FastAPI, UploadFile, File, HTTPException
import tempfile
from pydantic import BaseModel
from rag import AURA
from Pipeline.speech import transcribe_audio
import os
from typing import List, Optional

app = FastAPI(title="DAU RAG API")
aura = AURA()

class HistoryTurn(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[HistoryTurn]] = None

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"}

@app.post("/chat")
def chat(request: ChatRequest):
    history = (
        [turn.model_dump()
         for turn in request.history]
        if request.history
        else []
    )
    return aura.ask(question=request.question, history=history)


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
            content = await file.read()

            temp_file.write(content)

            temp_path = temp_file.name

        question = transcribe_audio(temp_path)

        return {"text": question}
        
    except Exception as e:
        print("Speech endpoint error:")
        print(e)

        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)