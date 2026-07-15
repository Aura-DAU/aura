# retrieval_metrics.md

# DAU AI Assistant – Retrieval Metrics Report

## Embedding Model Used

**BAAI/bge-base-en-v1.5**

* Dense semantic embedding model
* Embedding dimension: 768
* Used for generating vector representations of all document chunks

---

## Vector Database Used

**Qdrant Cloud**

* Vector type: Dense
* Similarity metric: Cosine Similarity
* Used for semantic retrieval of relevant document chunks

---

## Documents Indexed

**911**

The knowledge base consists of markdown documents generated from the scraped DAU website pages and supporting documents.

---

## Chunks Created

**15238**

Heirarchical heading-based semantic chunking with metadata enrichment.

---

## Chunk Size

**256 Tokens**

Maximum chunk size used during document processing.

---

## Chunk Overlap

**40 Tokens**

Token overlap was maintained between consecutive chunks to preserve contextual continuity across chunk boundaries.

---

## Top-K Retrieval

**Dynamic Top-K Retrieval with a maximum of 5 final context chunks.**

The retrieval depth is dynamically determined by the query planner based on the query intent and entity type. The final number of chunks included in the context ranges from 1 to 5, with a maximum of 5 chunks.

---

## Average Retrieval Latency

**0.341 seconds**

Average time taken to:

1. Generate query embedding
2. Perform Qdrant vector search
3. Retrieve Top-K matching chunks

Measured over multiple test queries.

---

## Summary

| Metric                    | Value                 |
| ------------------------- | --------------------- |
| Embedding Model           | BAAI/bge-base-en-v1.5 |
| Vector Database           | Qdrant Cloud          |
| Documents Indexed         | 911                   |
| Chunks Created            | 15238                 |
| Chunk Size                | 256 Tokens            |
| Chunk Overlap             | 40 Tokens             |
| Top-K Retrieval           | 1-5                   |
| Average Retrieval Latency | 0.341 seconds         |
