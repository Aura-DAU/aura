import os
import logging
import threading
from typing import Annotated, List

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from starlette.responses import JSONResponse

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

MAX_EMBED_TEXTS = int(os.getenv("MAX_EMBED_TEXTS", "64"))
MAX_RERANK_PAIRS = int(os.getenv("MAX_RERANK_PAIRS", "64"))
MAX_TEXT_CHARS = int(os.getenv("MAX_TEXT_CHARS", "8000"))
# Cap parallel GPU/CPU inference so a flood cannot OOM the node.
MAX_CONCURRENT_INFERENCE = max(1, int(os.getenv("MAX_CONCURRENT_INFERENCE", "2")))
# Reject bodies larger than this before parsing (default 1 MiB).
MAX_REQUEST_BYTES = max(64_000, int(os.getenv("MAX_REQUEST_BYTES", str(1 * 1024 * 1024))))

_inference_sem = threading.Semaphore(MAX_CONCURRENT_INFERENCE)

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
    texts: List[Annotated[str, Field(max_length=MAX_TEXT_CHARS)]] = Field(
        ..., max_length=MAX_EMBED_TEXTS
    )
    normalize: bool = True


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    model: str
    dimension: int


class RerankPairRequest(BaseModel):
    # Each item is [query, passage_text]
    pairs: List[
        Annotated[
            List[Annotated[str, Field(max_length=MAX_TEXT_CHARS)]],
            Field(min_length=2, max_length=2),
        ]
    ] = Field(..., max_length=MAX_RERANK_PAIRS)


class RerankResponse(BaseModel):
    scores: List[float]
    model: str


@app.middleware("http")
async def reject_oversized_bodies(request: Request, call_next):
    # Cheap Content-Length gate — do not buffer the body here.
    if request.method in ("POST", "PUT", "PATCH"):
        cl = request.headers.get("content-length")
        if cl is not None:
            try:
                if int(cl) > MAX_REQUEST_BYTES:
                    return JSONResponse({"detail": "Request body too large"}, status_code=413)
            except ValueError:
                return JSONResponse({"detail": "Invalid Content-Length"}, status_code=400)
    return await call_next(request)


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

    acquired = _inference_sem.acquire(blocking=False)
    if not acquired:
        raise HTTPException(status_code=503, detail="Embedding service busy — retry shortly")
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
        raise HTTPException(status_code=500, detail="Embedding failed")
    finally:
        _inference_sem.release()


@app.post("/rerank", response_model=RerankResponse)
def rerank_pairs(req: RerankPairRequest):
    if not reranker_model or not reranker_tokenizer:
        raise HTTPException(status_code=503, detail="Reranker model not loaded")
    if not req.pairs:
        return RerankResponse(scores=[], model=RERANKER_MODEL_NAME)

    acquired = _inference_sem.acquire(blocking=False)
    if not acquired:
        raise HTTPException(status_code=503, detail="Reranker service busy — retry shortly")
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
        raise HTTPException(status_code=500, detail="Reranking failed")
    finally:
        _inference_sem.release()
