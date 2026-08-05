import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Query-time embeddings MUST use the same model as ingestion-time
# embeddings or retrieval silently degrades — single source of truth.
from pipeline.ingestion.chunking.config import MODEL_NAME

from pipeline.retrieval.bm25_retriever import BM25Retriever
from pipeline.retrieval.rrf import fuse
from pipeline.retrieval.qdrant_client import build_index_adapter

logger = logging.getLogger(__name__)
TOP_K = 3

# One brief retry before local fallback: a 503 from node4's concurrency gate
# usually clears within a second, while the local SentenceTransformer fallback
# runs on CPU and may pay a first-time model load.
EMBED_REMOTE_ATTEMPTS = max(1, int(os.getenv("EMBED_REMOTE_ATTEMPTS", "2")))
EMBED_REMOTE_BACKOFF_S = max(0.0, float(os.getenv("EMBED_REMOTE_BACKOFF_S", "0.3")))


class Retriever:

    def __init__(self):

        load_dotenv()

        self.model = None

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
        
        # Phase A: dense vector search now goes through Qdrant instead of
        # Pinecone (see qdrant_client.py). build_index_adapter() returns an
        # object with the same .query(vector=, top_k=, include_metadata=,
        # filter=) shape pinecone.Index had, so nothing below this line
        # needed to change.
        self.index = build_index_adapter()

    def _local_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(MODEL_NAME)
        return self.model

    def embed_query(self, query: str) -> Optional[list[float]]:
        import time
        t0 = time.time()
        query_text = (
            "Represent this sentence for searching relevant passages: "
            + query
        )
        embedding_service_url = os.getenv("EMBEDDING_SERVICE_URL")
        embedding = None

        if embedding_service_url:
            import requests
            for attempt in range(1, EMBED_REMOTE_ATTEMPTS + 1):
                try:
                    resp = requests.post(
                        f"{embedding_service_url.rstrip('/')}/embed",
                        json={"texts": [query_text], "normalize": True},
                        timeout=5
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        if "embeddings" in data and len(data["embeddings"]) > 0:
                            embedding = data["embeddings"][0]
                        break
                    if resp.status_code != 503:
                        # Non-503 failures won't heal on retry — fall back now.
                        logger.warning(
                            "Remote embedding service returned HTTP %s. Falling back to local model.",
                            resp.status_code,
                        )
                        break
                    logger.warning(
                        "Remote embedding service busy (503), attempt %d/%d.",
                        attempt, EMBED_REMOTE_ATTEMPTS,
                    )
                except Exception as e:
                    logger.warning(
                        "Remote embedding service failed (attempt %d/%d): %s",
                        attempt, EMBED_REMOTE_ATTEMPTS, e,
                    )
                if attempt < EMBED_REMOTE_ATTEMPTS:
                    time.sleep(EMBED_REMOTE_BACKOFF_S)
            if embedding is None:
                logger.warning("Remote embedding service unavailable. Falling back to local model.")

        if embedding is None:
            try:
                query_embedding = self._local_model().encode(
                    [query_text],
                    normalize_embeddings=True,
                    convert_to_numpy=True
                )
                embedding = query_embedding[0].tolist()
            except Exception as e:
                logger.warning("Local embedding model failed: %s", e)
                embedding = None

        t_elapsed = time.time() - t0
        dim = len(embedding) if embedding else 0
        print(f"\n===== QUERY EMBEDDING =====\nDimension: {dim} | Time: {t_elapsed:.4f}s")
        return embedding

    def retrieve(
        self,
        query,
        top_k=TOP_K,
        metadata_filter=None,
        allowed_roles=None
    ):

        # Metadata filters include authorization and, for authenticated
        # students, hard academic applicability. Never disable the complete
        # filter: doing so would allow a maintenance flag to bypass scope.
        pinecone_filter = metadata_filter

        query_embedding_list = self.embed_query(query) if self.index else None

        dense_results = []
        if self.index and query_embedding_list is not None:
            try:
                results = self.index.query(
                    vector=query_embedding_list,
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

        print("\n" + "=" * 60)
        print("===== DENSE RESULTS (QDRANT) =====")
        if dense_results:
            for rank, item in enumerate(dense_results, start=1):
                meta = item.get("metadata", {})
                h_str = " / ".join(filter(None, [meta.get("h1"), meta.get("h2"), meta.get("h3")]))
                print(f"{rank}. score={item.get('score', 0.0):.4f} | chunk={item.get('id')}")
                print(f"   title={meta.get('title', 'N/A')}")
                print(f"   file={meta.get('source_file') or meta.get('relative_path', 'N/A')}")
                if h_str:
                    print(f"   headers={h_str}")
        else:
            print("   (No dense results returned)")
        print("=" * 60)

        if not self.bm25:
            return dense_results

        bm25_results = self.bm25.retrieve(
            query=query,
            top_k=top_k,
            metadata_filter=metadata_filter,
            allowed_roles=allowed_roles
        )

        print("\n" + "=" * 60)
        print("===== BM25 RESULTS =====")
        if bm25_results:
            for rank, item in enumerate(bm25_results, start=1):
                meta = item.get("metadata", {})
                h_str = " / ".join(filter(None, [meta.get("h1"), meta.get("h2"), meta.get("h3")]))
                print(f"{rank}. score={item.get('score', 0.0):.4f} | chunk={item.get('id')}")
                print(f"   title={meta.get('title', 'N/A')}")
                print(f"   file={meta.get('source_file') or meta.get('relative_path', 'N/A')}")
                if h_str:
                    print(f"   headers={h_str}")
        else:
            print("   (No BM25 results returned)")
        print("=" * 60)

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
