import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = "BAAI/bge-base-en-v1.5"
TOP_K = 3

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Connecting to Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def retrieve(query, top_k=TOP_K):
    # BGE models require a prefix for query embeddings in retrieval tasks
    prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
    query_embedding = model.encode(prefixed_query, normalize_embeddings=True).tolist()

    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

    return results["matches"]