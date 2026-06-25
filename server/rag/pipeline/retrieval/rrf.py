def fuse(
    dense_results,
    bm25_results,
    k=60
):
    """Reciprocal Rank Fusion of dense and BM25 result lists.

    Fix #5: rrf_score is now stored on every returned result dict so that
    downstream consumers (confidence router, reranker) see the true
    hybrid signal rather than the original pre-fusion score.
    """

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
    results = []
    for item in ranked:
        r = item["result"].copy()
        r["rrf_score"] = item["rrf_score"]
        results.append(r)

    return results