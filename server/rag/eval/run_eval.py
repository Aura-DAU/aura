#!/usr/bin/env python3
"""
DAU RAG Evaluation Script.

Evaluates the retrieval pipeline against a ground-truth Q&A dataset and
reports accuracy, precision@k, per-category breakdown, latency stats, and
an optional regression gate that fails CI if quality drops below thresholds.

Existing behaviour (accuracy via source-match) is preserved; precision@k
and the regression gate are additive extensions per the AURA spec.
"""
import csv
import json
import argparse
import requests
import time
import sys
from typing import List, Dict, Any


def clean_url(u: str) -> str:
    u = u.lower().strip()
    u = u.replace("https://", "").replace("http://", "")
    u = u.replace("www.", "")
    if u.endswith("/"):
        u = u[:-1]
    return u


# ---------------------------------------------------------------------------
# precision@k helpers
# ---------------------------------------------------------------------------

def _source_to_str(s) -> str:
    """Normalise a source entry (string or dict) to a comparable string."""
    if isinstance(s, dict):
        return clean_url(s.get("url", "") or s.get("title", "") or "")
    return clean_url(str(s))


def precision_at_k(retrieved_sources: List[Any], expected_source: str, k: int) -> float:
    """
    Precision@k for a single query.

    Returns 1.0 if the expected source appears in the top-k retrieved
    sources, 0.0 otherwise.  When expected_source is empty (no ground
    truth available) the question is skipped and None is returned.

    The metric is binary-relevance precision: we have exactly one relevant
    document per query (the expected source), so precision@k collapses to
    a binary hit/miss at rank k.
    """
    if not expected_source.strip():
        return None  # type: ignore[return-value]

    exp_clean = clean_url(expected_source)
    top_k = retrieved_sources[:k]
    for s in top_k:
        candidate = _source_to_str(s)
        if exp_clean and exp_clean in candidate:
            return 1.0
    return 0.0


def compute_precision_at_k(results: List[Dict[str, Any]], k: int) -> float:
    """
    Mean precision@k over all questions that have a ground-truth source.
    Questions without a ground-truth source are excluded from the average.
    """
    scores = []
    for r in results:
        raw_sources = r.get("raw_sources", [])
        expected    = r.get("expected_source", "")
        score = precision_at_k(raw_sources, expected, k)
        if score is not None:
            scores.append(score)
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def per_category_breakdown(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Return accuracy and question count broken down by category."""
    cats: Dict[str, Dict[str, Any]] = {}
    for r in results:
        cat = r.get("category", "uncategorised") or "uncategorised"
        if cat not in cats:
            cats[cat] = {"total": 0, "passed": 0}
        cats[cat]["total"] += 1
        if r.get("status") == "PASS":
            cats[cat]["passed"] += 1
    for cat, data in cats.items():
        data["accuracy_percent"] = round(
            data["passed"] / data["total"] * 100 if data["total"] else 0.0, 2
        )
    return cats


# ---------------------------------------------------------------------------
# Evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(
    api_url: str,
    csv_path: str,
    output_path: str,
    k: int = 3,
    min_accuracy: float = 0.0,
    min_precision_at_k: float = 0.0,
) -> bool:
    """
    Run the full evaluation and write results to output_path.

    Parameters
    ----------
    k               : Rank cutoff for precision@k (default 3).
    min_accuracy    : Regression gate — minimum required accuracy (0–100).
                      Pass 0.0 to disable.
    min_precision_at_k : Regression gate — minimum required precision@k (0–1).
                         Pass 0.0 to disable.

    Returns True if all regression gates pass, False otherwise.
    """
    print(f"Starting evaluation using dataset: {csv_path}")
    print(f"Target API Endpoint: {api_url}")
    print(f"Precision@k with k={k}")

    questions: List[Dict[str, str]] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)

    total  = len(questions)
    passed = 0
    failed = 0
    results: List[Dict[str, Any]] = []

    start_time = time.time()

    for i, q in enumerate(questions, 1):
        question_text   = q.get("Question", "")
        category        = q.get("Category", "")
        expected_source = q.get("Expected Source", "").strip()
        expected_answer = q.get("Expected Answer", "").strip()

        print(f"[{i}/{total}] Testing: {question_text[:50]}...")

        payload = {"question": question_text}

        try:
            response = requests.post(api_url, json=payload, timeout=400)
            latency  = response.elapsed.total_seconds()

            if response.status_code == 200:
                data = response.json()
                answer      = data.get("answer", "")
                raw_sources = data.get("sources", [])   # kept for precision@k

                # Normalise sources for display / source-match
                sources        = []
                source_matched = False

                for s in raw_sources:
                    if isinstance(s, dict):
                        url     = s.get("url", "") or ""
                        title   = s.get("title", "") or ""
                        section = s.get("section", "") or ""
                        sources.append(url if url else f"{title} - {section}")

                        exp_clean = clean_url(expected_source)
                        if exp_clean and (
                            exp_clean in clean_url(url) or
                            exp_clean in clean_url(title) or
                            exp_clean in clean_url(section)
                        ):
                            source_matched = True
                    elif isinstance(s, str):
                        sources.append(s.strip())
                        exp_clean = clean_url(expected_source)
                        if exp_clean and exp_clean in clean_url(s):
                            source_matched = True

                is_valid_answer = len(answer.strip()) > 0

                if source_matched and is_valid_answer:
                    status  = "PASS"
                    passed += 1
                else:
                    status  = "FAIL"
                    failed += 1

                # Compute per-question precision@k
                p_at_k = precision_at_k(raw_sources, expected_source, k)

                results.append({
                    "question":        question_text,
                    "category":        category,
                    "expected_source": expected_source,
                    "expected_answer": expected_answer,
                    "actual_answer":   answer,
                    "actual_sources":  sources,
                    "raw_sources":     raw_sources,   # needed for p@k computation
                    "precision_at_k":  p_at_k,
                    "latency_sec":     latency,
                    "status":          status,
                    "error":           None,
                })
            else:
                print(f"  -> Error: Received status code {response.status_code}")
                failed += 1
                results.append({
                    "question":        question_text,
                    "category":        category,
                    "expected_source": expected_source,
                    "expected_answer": expected_answer,
                    "actual_answer":   "",
                    "actual_sources":  [],
                    "raw_sources":     [],
                    "precision_at_k":  None,
                    "latency_sec":     0.0,
                    "status":          "FAIL",
                    "error":           f"HTTP status {response.status_code}",
                })
        except Exception as e:
            print(f"  -> Exception: {e}")
            failed += 1
            results.append({
                "question":        question_text,
                "category":        category,
                "expected_source": expected_source,
                "expected_answer": expected_answer,
                "actual_answer":   "",
                "actual_sources":  [],
                "raw_sources":     [],
                "precision_at_k":  None,
                "latency_sec":     0.0,
                "status":          "FAIL",
                "error":           str(e),
            })

        # Space out requests to stay under Groq API TPM rate limits
        time.sleep(1.0)

    total_time   = time.time() - start_time
    accuracy     = (passed / total) * 100 if total > 0 else 0.0
    avg_latency  = sum(r["latency_sec"] for r in results) / len(results) if results else 0.0
    mean_p_at_k  = compute_precision_at_k(results, k)
    cat_breakdown = per_category_breakdown(results)

    summary = {
        "metrics": {
            "total_questions":    total,
            "passed":             passed,
            "failed":             failed,
            "accuracy_percent":   round(accuracy, 2),
            "precision_at_k":     round(mean_p_at_k, 4),
            "k":                  k,
            "total_time_sec":     round(total_time, 2),
            "avg_latency_sec":    round(avg_latency, 3),
            "regression_gate": {
                "min_accuracy":       min_accuracy,
                "min_precision_at_k": min_precision_at_k,
            },
        },
        "per_category": cat_breakdown,
        "results": results,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*50)
    print("EVALUATION COMPLETED")
    print("="*50)
    print(f"Total Questions:   {total}")
    print(f"Passed:            {passed}")
    print(f"Failed:            {failed}")
    print(f"Accuracy:          {accuracy:.2f}%")
    print(f"Precision@{k}:      {mean_p_at_k:.4f}")
    print(f"Avg Latency:       {avg_latency:.3f} seconds")
    print(f"Results saved to:  {output_path}")
    print("="*50)

    # ── Per-category summary ──────────────────────────────────────────────
    if cat_breakdown:
        print("\nPer-category breakdown:")
        for cat, data in sorted(cat_breakdown.items()):
            print(f"  {cat:40s}  {data['passed']:3d}/{data['total']:3d}  ({data['accuracy_percent']:.1f}%)")

    # ── Regression gate ───────────────────────────────────────────────────
    gate_passed = True
    if min_accuracy > 0.0 and accuracy < min_accuracy:
        print(f"\n[REGRESSION GATE FAILED] accuracy {accuracy:.2f}% < required {min_accuracy:.2f}%")
        gate_passed = False
    if min_precision_at_k > 0.0 and mean_p_at_k < min_precision_at_k:
        print(
            f"\n[REGRESSION GATE FAILED] precision@{k} {mean_p_at_k:.4f} "
            f"< required {min_precision_at_k:.4f}"
        )
        gate_passed = False

    if gate_passed:
        print("\n[REGRESSION GATE] All quality thresholds met.")

    return gate_passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DAU RAG Evaluation Script")
    parser.add_argument(
        "--api-url", default="http://localhost:8000/chat",
        help="RAG Chat API endpoint URL",
    )
    parser.add_argument(
        "--csv", default="server/rag/eval/representative_dataset.csv",
        help="Path to evaluation dataset CSV",
    )
    parser.add_argument(
        "--output", default="server/rag/eval/representative_results.json",
        help="Path to save output JSON",
    )
    parser.add_argument(
        "--k", type=int, default=3,
        help="Rank cutoff for precision@k (default: 3)",
    )
    parser.add_argument(
        "--min-accuracy", type=float, default=0.0,
        help="Regression gate: minimum required accuracy %% (0=disabled)",
    )
    parser.add_argument(
        "--min-precision-at-k", type=float, default=0.0,
        help="Regression gate: minimum required precision@k 0-1 (0=disabled)",
    )

    args = parser.parse_args()
    gate_ok = run_evaluation(
        api_url=args.api_url,
        csv_path=args.csv,
        output_path=args.output,
        k=args.k,
        min_accuracy=args.min_accuracy,
        min_precision_at_k=args.min_precision_at_k,
    )
    sys.exit(0 if gate_ok else 1)
