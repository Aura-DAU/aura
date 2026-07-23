import os
import logging
from typing import List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedding-reranker-service")

app = FastAPI(
    title="AURA Embedding & Reranker Service",
    description="Standalone microservice for Node 4 hosting dense embeddings (BGE-M3) and cross-encoder reranking (BGE-Reranker-v2-m3).",
    version="1.0.0"
)

# Configuration from Environment
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-base-en-v1.5")
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-v2-m3")

if os.getenv("RERANKER_DEVICE"):
    DEVICE_NAME = os.getenv("RERANKER_DEVICE")
elif torch.cuda.is_available():
    DEVICE_NAME = "cuda"
elif torch.backends.mps.is_available():
    DEVICE_NAME = "mps"
else:
    DEVICE_NAME = "cpu"

device = torch.device(DEVICE_NAME)

logger.info(f"Initializing models on device: {device}")

try:
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=str(device))
    logger.info(f"Loaded Embedding Model: {EMBEDDING_MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to load embedding model {EMBEDDING_MODEL_NAME}: {e}")
    embedding_model = None

try:
    reranker_tokenizer = AutoTokenizer.from_pretrained(RERANKER_MODEL_NAME)
    reranker_model = AutoModelForSequenceClassification.from_pretrained(RERANKER_MODEL_NAME).to(device)
    reranker_model.eval()
    logger.info(f"Loaded Reranker Model: {RERANKER_MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to load reranker model {RERANKER_MODEL_NAME}: {e}")
    reranker_tokenizer = None
    reranker_model = None


class EmbedRequest(BaseModel):
    texts: List[str]
    normalize: bool = True


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int


class RerankPairRequest(BaseModel):
    pairs: List[List[str]]  # Each item is [query, passage_text]


class RerankResponse(BaseModel):
    scores: List[float]
    model: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "device": str(device),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "embedding_loaded": embedding_model is not None,
        "reranker_model": RERANKER_MODEL_NAME,
        "reranker_loaded": reranker_model is not None,
    }


@app.post("/embed", response_model=EmbedResponse)
def embed_texts(req: EmbedRequest):
    if not embedding_model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded")
    if not req.texts:
        return EmbedResponse(embeddings=[], model=EMBEDDING_MODEL_NAME, dimension=0)
    
    try:
        embeddings = embedding_model.encode(
            req.texts,
            normalize_embeddings=req.normalize,
            convert_to_numpy=True
        ).tolist()
        dimension = len(embeddings[0]) if embeddings else 0
        return EmbedResponse(
            embeddings=embeddings,
            model=EMBEDDING_MODEL_NAME,
            dimension=dimension
        )
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rerank", response_model=RerankResponse)
def rerank_pairs(req: RerankPairRequest):
    if not reranker_model or not reranker_tokenizer:
        raise HTTPException(status_code=503, detail="Reranker model not loaded")
    if not req.pairs:
        return RerankResponse(scores=[], model=RERANKER_MODEL_NAME)
    
    try:
        inputs = reranker_tokenizer(
            req.pairs,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            logits = reranker_model(**inputs).logits.squeeze(-1)
            if logits.ndim == 0:
                scores = [float(logits.item())]
            else:
                scores = logits.tolist()
        return RerankResponse(scores=scores, model=RERANKER_MODEL_NAME)
    except Exception as e:
        logger.error(f"Reranking error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
