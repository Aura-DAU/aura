import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from dotenv import load_dotenv
from pinecone import Pinecone
from tqdm import tqdm


# ==================================================
# CONFIG
# ==================================================

EMBEDDINGS_FILE = "../../vector_store/embeddings.npy"
METADATA_FILE = "../../vector_store/metadata.json"

BATCH_SIZE = 100


# ==================================================
# HELPERS
# ==================================================

def chunk_list(items, batch_size):

    for i in range(0, len(items), batch_size):

        yield items[i:i + batch_size]


# ==================================================
# MAIN
# ==================================================

def main():

    load_dotenv()

    api_key = os.getenv(
        "PINECONE_API_KEY"
    )

    index_name = os.getenv("PINECONE_INDEX")

    if not api_key:

        raise ValueError(
            "PINECONE_API_KEY not found"
        )

    print("Connecting to Pinecone...")

    pc = Pinecone(
        api_key=api_key
    )

    index = pc.Index(
        index_name
    )

    print("Loading embeddings...")

    embeddings = np.load(
        EMBEDDINGS_FILE
    )

    print("Loading metadata...")

    with open(
        METADATA_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        metadata = json.load(f)

    assert len(embeddings) == len(metadata)

    print(
        f"Preparing "
        f"{len(metadata)} vectors..."
    )

    vectors = []

    for embedding, chunk in zip(
        embeddings,
        metadata
    ):

        vector = {

            "id":
                chunk["chunk_id"],

            "values":
                embedding.tolist(),

            "metadata": {

                "text":
                    chunk["text"],
                
                "cluster":
                    chunk.get("cluster"),

                "subclusters":
                    chunk.get("subclusters"),

                "document_type":
                    chunk.get(
                        "document_type"
                    )
            }
        }

        # Coordinate metadata
        if chunk.get("document_id"):
            vector["metadata"]["document_id"] = chunk["document_id"]

        if chunk.get("chunk_index") is not None:
            vector["metadata"]["chunk_index"] = int(chunk["chunk_index"])

        if chunk.get("total_chunks") is not None:
            vector["metadata"]["total_chunks"] = int(chunk["total_chunks"])

        # Optional metadata

        if chunk.get("category"):
            vector["metadata"]["category"] = chunk["category"]

        if chunk.get("title"):
            vector["metadata"]["title"] = chunk["title"]

        if chunk.get("url"):
            vector["metadata"]["url"] = chunk["url"]

        if chunk.get(
            "faculty_name"
        ):

            vector["metadata"][
                "faculty_name"
            ] = chunk[
                "faculty_name"
            ]

        if chunk.get(
            "program_name"
        ):
            
            vector["metadata"][
                "program_name"
            ] = chunk[
                "program_name"
            ]

        if chunk.get(
            "section_type"
        ):
            
            vector["metadata"][
                "section_type"
            ] = chunk[
                "section_type"
            ]

        if chunk.get(
            "event_name"
        ):

            vector["metadata"][
                "event_name"
            ] = chunk[
                "event_name"
            ]

        if chunk.get(
            "event_date"
        ):

            vector["metadata"][
                "event_date"
            ] = chunk[
                "event_date"
            ]

        if chunk.get(
            "venue"
        ):

            vector["metadata"][
                "venue"
            ] = chunk[
                "venue"
            ]
        
        if chunk.get(
            "semester"
        ):

            vector["metadata"][
                "semester"
            ] = chunk[
                "semester"
            ]


        if chunk.get(
            "course_code"
        ):

            vector["metadata"][
                "course_code"
            ] = chunk[
                "course_code"
            ]


        if chunk.get(
            "course_name"
        ):

            vector["metadata"][
                "course_name"
            ] = chunk[
                "course_name"
            ]


        if chunk.get(
            "course_type"
        ):

            vector["metadata"][
                "course_type"
            ] = chunk[
                "course_type"
            ]


        if chunk.get(
            "credits"
        ):

            vector["metadata"][
                "credits"
            ] = chunk[
                "credits"
            ]
        
        if chunk.get("h1"):
            vector["metadata"]["h1"] = chunk["h1"]
        
        if chunk.get("h2"):
            vector["metadata"]["h2"] = chunk["h2"]

        if chunk.get("h3"):
            vector["metadata"]["h3"] = chunk["h3"]

        if chunk.get("scraped_date"):
            vector["metadata"]["scraped_date"] = chunk["scraped_date"]

        if chunk.get("start_line") is not None:
            vector["metadata"]["start_line"] = int(chunk["start_line"])

        if chunk.get("end_line") is not None:
            vector["metadata"]["end_line"] = int(chunk["end_line"])

        if chunk.get("document_year") is not None:
            try:
                vector["metadata"]["document_year"] = int(chunk["document_year"])
            except (ValueError, TypeError):
                vector["metadata"]["document_year"] = str(chunk["document_year"])

        vectors.append(
            vector
        )

    batches = list(chunk_list(vectors, BATCH_SIZE))
    print(
        f"Uploading {len(vectors)} vectors in {len(batches)} batches of {BATCH_SIZE}..."
    )

    # Use ThreadPoolExecutor for parallel Pinecone upserts
    with ThreadPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(index.upsert, vectors=batch): i for i, batch in enumerate(batches)}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Uploading"):
            try:
                future.result()
            except Exception as e:
                batch_idx = futures[future]
                print(f"\n[ERROR] Batch {batch_idx} failed to upload: {e}")

    print("\nUpload complete!")

    stats = (
        index.describe_index_stats()
    )

    print("\nIndex Stats:")
    print(stats)


if __name__ == "__main__":
    main()