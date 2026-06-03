# retrieval_metrics.md

# DAU AI Assistant – Retrieval Metrics Report

## Embedding Model Used

**BAAI/bge-base-en-v1.5**

* Dense semantic embedding model
* Embedding dimension: 768
* Used for generating vector representations of all document chunks

---

## Vector Database Used

**Pinecone**

* Vector type: Dense
* Similarity metric: Cosine Similarity
* Used for semantic retrieval of relevant document chunks

---

## Documents Indexed

**885**

The knowledge base consists of markdown documents generated from the scraped DAU website pages and supporting documents.

---

## Chunks Created

**8070**

Header-aware chunking was used to preserve document structure while maintaining semantic coherence.

---

## Chunk Size

**600 Tokens**

Maximum chunk size used during document processing.

---

## Chunk Overlap

**75 Tokens**

Token overlap was maintained between consecutive chunks to preserve contextual continuity across chunk boundaries.

---

## Top-K Retrieval

**20**

For each user query, the top 20 most relevant chunks are retrieved from Pinecone and provided to the language model for answer generation.

---

## Average Retrieval Latency

**0.405 seconds**

Average time taken to:

1. Generate query embedding
2. Perform Pinecone vector search
3. Retrieve Top-K matching chunks

Measured over multiple test queries.

---

## Summary

| Metric                    | Value                 |
| ------------------------- | --------------------- |
| Embedding Model           | BAAI/bge-base-en-v1.5 |
| Vector Database           | Pinecone              |
| Documents Indexed         | 885                   |
| Chunks Created            | 8070                  |
| Chunk Size                | 600 Tokens            |
| Chunk Overlap             | 75 Tokens             |
| Top-K Retrieval           | 20                    |
| Average Retrieval Latency | 0.405 seconds         |
