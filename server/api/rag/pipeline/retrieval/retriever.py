import os

from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# Query-time embeddings MUST use the same model as ingestion-time
# embeddings or retrieval silently degrades — single source of truth.
from pipeline.ingestion.chunking.config import MODEL_NAME

from pipeline.retrieval.bm25_retriever import BM25Retriever
from pipeline.retrieval.rrf import fuse

TOP_K = 3


class Retriever:

    def __init__(self):

        load_dotenv()

        self.model = SentenceTransformer(
            MODEL_NAME
        )

        self.bm25 = BM25Retriever(
            "pipeline/vector_store/metadata.json"
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