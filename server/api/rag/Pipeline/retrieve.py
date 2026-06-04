import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

load_dotenv()

MODEL_NAME = "BAAI/bge-base-en-v1.5"
TOP_K = 20

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

print("Connecting to Pinecone...")
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

def retrieve(query, top_k=TOP_K):
    query_embedding = model.encode(query, normalize_embeddings=True).tolist()

    results = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)

    return results["matches"]