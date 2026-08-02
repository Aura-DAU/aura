def fuse(
    dense_results,
    bm25_results,
    k=60
):
    # Reciprocal Rank Fusion of dense and BM25 result lists.
    # Fix #5: rrf_score is now stored on every returned result dict so that
    # hybrid signal rather than the original pre-fusion score.

    fused = {}

    # Dense contribution
    for rank, result in enumerate(
        dense_results,
        start=1
    ):

        chunk_id = result["id"]

        if chunk_id not in fused:

            fused[chunk_id] = {

                "result": result,

                "rrf_score": 0.0
            }

        fused[chunk_id][
            "rrf_score"
        ] += 1 / (k + rank)

    # BM25 contribution
    for rank, result in enumerate(
        bm25_results,
        start=1
    ):

        chunk_id = result["id"]

        if chunk_id not in fused:

            fused[chunk_id] = {

                "result": result,

                "rrf_score": 0.0
            }

        fused[chunk_id][
            "rrf_score"
        ] += 1 / (k + rank)

    ranked = sorted(
        fused.values(),
        key=lambda x: x["rrf_score"],
        reverse=True
    )

    # Fix #5: attach rrf_score to each result dict so it propagates
    # to the confidence router and reranker (previously it was discarded).
    # Fix RRF1: BM25-only chunks (not in Pinecone top_k) have no cosine_score
    # field. The router reads c.get("cosine_score") → None → 0.0, so a
    # BM25-only chunk at the top of the fused list always contributes 0.0 to
    # top_cosine even if it is highly relevant. Guarantee the field exists on
    # every result so the router signal is never silently zeroed.
    dense_ranks = {res["id"]: i for i, res in enumerate(dense_results, start=1)}
    bm25_ranks = {res["id"]: i for i, res in enumerate(bm25_results, start=1)}

    results = []
    for item in ranked:
        r = item["result"].copy()
        r["rrf_score"] = item["rrf_score"]
        if "cosine_score" not in r:
            r["cosine_score"] = 0.0
        results.append(r)

    print("\n" + "=" * 60)
    print("===== RRF (RECIPROCAL RANK FUSION) RESULTS =====")
    for rank, r in enumerate(results, start=1):
        cid = r["id"]
        meta = r.get("metadata", {})
        d_rank = dense_ranks.get(cid, "N/A")
        b_rank = bm25_ranks.get(cid, "N/A")
        print(f"{rank}. rrf_score={r.get('rrf_score', 0.0):.6f} | Dense Rank: {d_rank} | BM25 Rank: {b_rank}")
        print(f"   chunk={cid}")
        print(f"   title={meta.get('title', 'N/A')}")
        print(f"   file={meta.get('source_file') or meta.get('relative_path', 'N/A')}")
    print("=" * 60)

    return results