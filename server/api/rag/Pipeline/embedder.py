import json
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-base-en-v1.5"

def load_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)
    

def generate_embeddings(chunks):
    print(f"Loading {MODEL_NAME}...")

    model = SentenceTransformer(MODEL_NAME)
    
    print(f"Generating embeddings for {len(chunks)} chunks...")

    embeddings = []

    for idx, chunk in enumerate(chunks):
        embedding = model.encode(
            chunk["content"],
            normalize_embeddings=True
        )

        embeddings.append(
            {
                "chunk_id": chunk["chunk_id"],
                "document_id": chunk["document_id"],
                "embedding": embedding.tolist(),
                "metadata": {
                    "title": chunk["title"],
                    "category": chunk["category"],
                    "url": chunk["url"],
                    "heading": chunk["heading"],
                    "section_path": chunk["section_path"],
                    "source_file": chunk["source_file"],
                    "scraped_date": chunk["scraped_date"],
                    "token_count": chunk["token_count"],
                    "content": chunk["content"]
                }
            }
        )

        if (idx + 1) % 10 == 0:
            print(f"{idx+1}/{len(chunks)} completed")
    
    return embeddings


def save_embeddings(embeddings, filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    chunks = load_chunks("../knowledge_index/chunks.json")

    embeddings = generate_embeddings(chunks)

    save_embeddings(embeddings, "../knowledge_index/embeddings.json")

    print(f"\nSaved {len(embeddings)} embeddings")

    print(
        f"Embedding dimension: "
        f"{len(embeddings[0]['embedding'])}"
    )
