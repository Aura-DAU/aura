import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Query-time embeddings MUST use the same model as ingestion-time
# embeddings or retrieval silently degrades — single source of truth.
from pipeline.ingestion.chunking.config import MODEL_NAME

from pipeline.retrieval.bm25_retriever import BM25Retriever
from pipeline.retrieval.rrf import fuse

logger = logging.getLogger(__name__)
TOP_K = 3

# BGE-style instruction prefix — must be identical for every query embedding
# (single source of truth for retrieve() and encode_queries()).
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class Retriever:

    def __init__(self):

        load_dotenv()

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        metadata_path = (
            Path(__file__).resolve().parent.parent
            / "vector_store"
            / "metadata.json"
        )

        self.bm25 = None
        if metadata_path.exists():
            try:
                self.bm25 = BM25Retriever(
                    str(metadata_path)
                )
                logger.info("BM25 Retriever initialized successfully from local metadata.")
            except Exception as e:
                logger.warning("Failed to initialize BM25 Retriever: %s. Sparse search will be disabled.", e)
        else:
            logger.warning(
                "Local metadata.json not found at %s. BM25 sparse search is disabled. Run sync_db.py to generate it.",
                metadata_path
            )
        
        self.index = None
        try:
            pc = Pinecone(
                api_key=os.getenv(
                    "PINECONE_API_KEY"
                )
            )
            self.index = pc.Index(
                os.getenv(
                    "PINECONE_INDEX"
                )
            )
            logger.info("Pinecone Index initialized successfully.")
        except Exception as e:
            logger.warning("Failed to initialize Pinecone Index: %s. Dense search will be disabled.", e)

    def encode_queries(self, queries):
        # Embed many query strings in ONE forward pass. Batching N texts is
        # far cheaper than N sequential encode() calls, and callers can pass
        # each row back into retrieve() via precomputed_embedding.
        return self.model.encode(
            [QUERY_PREFIX + q for q in queries],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

    def retrieve(
        self,
        query,
        top_k=TOP_K,
        metadata_filter=None,
        allowed_roles=None,
        precomputed_embedding=None
    ):

        # TEMPORARY FIX: Pinecone currently lacks the 'allowed_roles' metadata field,
        # so applying the DLS metadata_filter returns 0 chunks for ALL queries.
        # Disabling filter until vectors are re-ingested with correct metadata.
        pinecone_filter = metadata_filter
        if os.getenv("DISABLE_PINECONE_DLS_FILTER", "false").lower() == "true":
            pinecone_filter = None

        if precomputed_embedding is not None:
            query_embedding = precomputed_embedding
        else:
            query_embedding = self.encode_queries([query])[0]

        dense_results = []
        if self.index:
            try:
                results = self.index.query(
                    vector=query_embedding.tolist(),
                    top_k=top_k,
                    include_metadata=True,
                    filter=pinecone_filter
                )
                for match in results["matches"]:
                    dense_results.append(
                        {
                            "id":
                                match["id"],

                            # Fix #1A: store the raw Pinecone cosine score separately
                            # so the confidence router can use it even after RRF fusion
                            # overwrites 'score' with the hybrid rrf_score.
                            "score":
                                match["score"],

                            "cosine_score":
                                match["score"],

                            "metadata":
                                match["metadata"]
                        }
                    )
            except Exception as e:
                logger.warning("Pinecone query failed: %s", e)

        if not self.bm25:
            return dense_results

        bm25_results = self.bm25.retrieve(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            allowed_roles=allowed_roles
        )

        fused_results = fuse(
            dense_results,
            bm25_results
        )

        return fused_results

    def retrieve_by_ids(
        self,
        chunk_ids: list[str],
    ) -> list[dict]:
        # Hydrate a list of chunk IDs into full result dicts using the local
        # BM25 metadata store.  Used by the retrieval pipeline to pull
        # score is set to 0.0 (entity-match is boolean; reranker scores it).
        if not self.bm25 or not chunk_ids:
            return []

        id_set = set(chunk_ids)
        results = []

        for chunk in self.bm25.chunks:
            cid = chunk.get("chunk_id")
            if cid in id_set:
                results.append({
                    "id": cid,
                    "score": 0.0,
                    "metadata": chunk,
                })

        return results