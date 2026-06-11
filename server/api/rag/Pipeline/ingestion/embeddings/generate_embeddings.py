import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ==================================================
# CONFIG
# ==================================================

MODEL_NAME = "BAAI/bge-base-en-v1.5"

CHUNKS_FILE = "../../../processed_chunks/chunks.json"


EMBEDDINGS_FILE = "../../vector_store/embeddings.npy"
METADATA_FILE = "../../vector_store/metadata.json"


# ==================================================
# HELPERS
# ==================================================

def load_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


# ==================================================
# MAIN
# ==================================================

def main():

    print(f"Loading model: {MODEL_NAME}")

    model = SentenceTransformer(MODEL_NAME)

    print("Loading chunks...")

    chunks = load_chunks(CHUNKS_FILE)

    print(f"Loaded {len(chunks)} chunks")

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    print("Generating embeddings...")

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True
    )

    embeddings = embeddings.astype("float32")

    print(
        f"\nEmbedding shape: "
        f"{embeddings.shape}"
    )

    # ==========================================
    # SAVE OUTPUTS
    # ==========================================

    Path("../../vector_store").mkdir(
        parents=True,
        exist_ok=True
    )

    np.save(
        EMBEDDINGS_FILE,
        embeddings
    )

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            chunks,
            f,
            ensure_ascii=False
        )

    print("\nSaved embeddings")

    print(
        f"Embeddings -> {EMBEDDINGS_FILE}"
    )

    print(
        f"Metadata -> {METADATA_FILE}"
    )


if __name__ == "__main__":
    main()