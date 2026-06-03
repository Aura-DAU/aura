import json
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX")

if not PINECONE_API_KEY:
    raise ValueError(
        "PINECONE_API_KEY not found"
    )

if not INDEX_NAME:
    raise ValueError(
        "PINECONE_INDEX not found"
    )

pc = Pinecone(api_key=PINECONE_API_KEY)

index = pc.Index(INDEX_NAME)

print("Loading embeddings...")

with open("../knowledge_index/embeddings.json", "r", encoding="utf-8") as f:
    embeddings = json.load(f)

print(f"Loaded {len(embeddings)} embeddings")

vectors = []

for item in embeddings:
    vectors.append(
        {
            "id": item["chunk_id"],
            "values": item["embedding"],
            "metadata": item["metadata"]
        }
    )

print(f"Prepared {len(vectors)} vectors")

BATCH_SIZE = 100

for i in range(0, len(vectors), BATCH_SIZE):
    batch = vectors[i:i+BATCH_SIZE]

    index.upsert(vectors=batch)

    print(f"Uploaded {i + len(batch)}/{len(vectors)}")

print("\nUpload complete!")