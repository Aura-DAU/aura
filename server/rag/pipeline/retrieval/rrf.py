def fuse(
    dense_results,
    bm25_results,
    k=60
):

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

    return [
        item["result"]
        for item in ranked
    ]