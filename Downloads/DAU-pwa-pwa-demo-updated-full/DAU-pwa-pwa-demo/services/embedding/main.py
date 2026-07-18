"""
AURA Embedding Service
======================
Exposes a single HTTP endpoint that converts text into dense embeddings using
the same model (BAAI/bge-base-en-v1.5) as the ingestion pipeline.

Architecture PDF — Section 9: "Embedding Generation Service"
Container name: aura-embedding
Endpoint: POST /embed  →  { "embeddings": [[float, ...], ...] }

The backend's Retriever currently loads SentenceTransformer inline. When
EMBEDDING_SERVICE_URL is set in the backend's environment, the Retriever
should call this service instead of loading the model locally — keeping GPU
resources on Node 4 dedicated to retrieval AI (not shared with the API process
on Node 1).
"""
import os
import logging
from typing import List

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aura-embedding")

MODEL_NAME  = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
DEVICE      = os.getenv("EMBEDDING_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE  = int(os.getenv("EMBEDDING_BATCH_SIZE", "64"))
MAX_TEXTS   = int(os.getenv("EMBEDDING_MAX_TEXTS", "512"))

app = FastAPI(title="AURA Embedding Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

logger.info("Loading embedding model %s on device %s …", MODEL_NAME, DEVICE)
_model = SentenceTransformer(MODEL_NAME, device=DEVICE)
_model.eval()
logger.info("Embedding model ready.")


class EmbedRequest(BaseModel):
    texts:    List[str]
    normalize: bool = True   # BGE models perform best with L2-normalized vectors


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model:      str
    dim:        int


@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    if not req.texts:
        raise HTTPException(status_code=400, detail="texts list must not be empty")
    if len(req.texts) > MAX_TEXTS:
        raise HTTPException(
            status_code=413,
            detail=f"Too many texts — max {MAX_TEXTS} per request",
        )
    with torch.no_grad():
        vecs = _model.encode(
            req.texts,
            batch_size=BATCH_SIZE,
            normalize_embeddings=req.normalize,
            show_progress_bar=False,
        )
    return EmbedResponse(
        embeddings=vecs.tolist(),
        model=MODEL_NAME,
        dim=vecs.shape[1],
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": DEVICE}
