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

    def retrieve(
        self,
        query,
        top_k=TOP_K,
        metadata_filter=None
    ):

        query_embedding = self.model.encode(
            [
                "Represent this sentence for searching relevant passages: "
                + query
            ],
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        results = self.index.query(
            vector=query_embedding[0].tolist(),
            top_k=top_k,
            include_metadata=True,
            filter=metadata_filter
        )

        chunks = []

        for match in results["matches"]:

            chunks.append(
                {
                    "id": 
                        match["id"],
                        
                    "score":
                        match["score"],

                    "metadata":
                        match["metadata"]
                }
            )

        dense_results = chunks

        if not self.bm25:
            return dense_results

        bm25_results = self.bm25.retrieve(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter
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
        """
        Hydrate a list of chunk IDs into full result dicts using the local
        BM25 metadata store.  Used by the retrieval pipeline to pull
        entity-matched chunks without an extra Pinecone query.

        Returns only chunks whose IDs are present in the local store.
        score is set to 0.0 (entity-match is boolean; reranker scores it).
        """
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