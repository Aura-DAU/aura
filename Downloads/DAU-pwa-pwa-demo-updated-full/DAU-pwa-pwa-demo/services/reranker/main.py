"""
AURA Cross-Encoder Reranker Service
=====================================
Exposes an HTTP endpoint that scores (query, passage) pairs using the
BAAI/bge-reranker-v2-m3 cross-encoder — the same model used inline in the
backend's Reranker class.

Architecture PDF — Section 11: "Cross-Encoder Re-ranking Service"
Container name: aura-reranker
Endpoint: POST /rerank  →  scored + sorted candidates

When RERANKER_SERVICE_URL is set in the backend environment, the Reranker
class should call this service instead of loading the model locally, keeping
the heavy GPU work on Node 4 (RTX 5080).
"""
import os
import logging
from typing import List

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aura-reranker")

MODEL_NAME  = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
DEVICE_STR  = os.getenv("RERANKER_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
DEVICE      = torch.device(DEVICE_STR)
MAX_PAIRS   = int(os.getenv("RERANKER_MAX_PAIRS", "200"))

app = FastAPI(title="AURA Reranker Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

logger.info("Loading cross-encoder %s on device %s …", MODEL_NAME, DEVICE_STR)
_tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
_model     = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME).to(DEVICE)
_model.eval()
logger.info("Cross-encoder ready.")


class Candidate(BaseModel):
    id:      str
    text:    str
    # Optional metadata forwarded from the retriever
    score:   float = 0.0
    metadata: dict = {}


class RerankRequest(BaseModel):
    query:      str
    candidates: List[Candidate]
    top_k:      int = 8


class RankedCandidate(BaseModel):
    id:          str
    text:        str
    score:       float   # raw cross-encoder logit
    rank:        int
    metadata:    dict


class RerankResponse(BaseModel):
    results: List[RankedCandidate]
    model:   str


@app.post("/rerank", response_model=RerankResponse)
def rerank(req: RerankRequest):
    if not req.candidates:
        return RerankResponse(results=[], model=MODEL_NAME)
    if len(req.candidates) > MAX_PAIRS:
        raise HTTPException(
            status_code=413,
            detail=f"Too many candidates — max {MAX_PAIRS} per request",
        )

    pairs = [[req.query, c.text] for c in req.candidates]

    with torch.no_grad():
        encoded = _tokenizer(
            pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        ).to(DEVICE)
        logits = _model(**encoded).logits.squeeze(-1)
        scores = logits.float().cpu().tolist()

    # Sort descending by score
    ranked = sorted(
        zip(req.candidates, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    top = ranked[: req.top_k]
    return RerankResponse(
        results=[
            RankedCandidate(
                id=c.id,
                text=c.text,
                score=s,
                rank=i + 1,
                metadata=c.metadata,
            )
            for i, (c, s) in enumerate(top)
        ],
        model=MODEL_NAME,
    )


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME, "device": DEVICE_STR}
