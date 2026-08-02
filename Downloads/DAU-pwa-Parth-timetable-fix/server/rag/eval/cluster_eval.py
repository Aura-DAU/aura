#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# cluster_eval.py — Cluster-Based RAG Evaluation for Faculty Intelligence Platform
# Evaluates the Aura RAG bot against questions derived from the Faculty Cluster
# diagram.
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import csv
import json
import argparse
import requests
import time
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

# ── Cluster Level descriptions ─────────────────────────────────────────────────
LEVEL_DESC = {
    "Level1_Static": "Level 1 – Static Information (Complete)",
    "Level2_Dynamic": "Level 2 – Dynamic / Continuously Updating (Initiated)",
    "Level3_Human": "Level 3 – Human-Provided Knowledge (Complete)",
    "Level4_Future": "Level 4 – Future Integrations & Automation (Planned)",
    "Cross_Cluster": "Cross-Cluster / Multi-Level",
}

FALLBACK_PHRASES = [
    "i could not find",
    "sorry, i encountered an error",
    "i'm having trouble retrieving",
    "i can only help with questions about",
    "please try again in a moment",
    "contact dau directly",
    "i don't have information",
    "no information available",
    "not found in my knowledge",
]


def clean_url(u: str) -> str:
    u = u.lower().strip()
    u = u.replace("https://", "").replace("http://", "").replace("www.", "")
    if u.endswith("/"):
        u = u[:-1]
    return u


def check_answer_quality(answer: str, expected_answer: str) -> str:
    # PASS / PARTIAL / FAIL verdict based on content coverage.
    if not answer or len(answer.strip()) < 10:
        return "FAIL"
    answer_lower = answer.lower()
    for phrase in FALLBACK_PHRASES:
        if phrase in answer_lower:
            return "FAIL"
    if not expected_answer:
        return "PARTIAL"
    expected_tokens = [
        t.lower().strip(".,;:()[]\"'")
        for t in expected_answer.split()
        if len(t) > 3
    ]
    if not expected_tokens:
        return "PARTIAL"
    hits = sum(1 for t in expected_tokens if t in answer_lower)
    coverage = hits / len(expected_tokens)
    if coverage >= 0.30:
        return "PASS"
    return "PARTIAL"


def run_evaluation(api_url: str, csv_path: str, output_path: str) -> None:
    start_ts = datetime.now().isoformat()
    print(f"\n{'='*65}")
    print(f" AURA CLUSTER EVALUATION — Faculty Intelligence AI Platform")
    print(f" Started : {start_ts}")
    print(f" CSV     : {csv_path}")
    print(f" API     : {api_url}")
    print(f"{'='*65}\n")

    questions: List[Dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)

    total = len(questions)
    passed = partial = failed = 0
    results: List[Dict[str, Any]] = []
    cat_stats: Dict[str, Dict[str, int]] = {}
    level_stats: Dict[str, Dict[str, int]] = {}
    topic_stats: Dict[str, Dict[str, int]] = {}

    start_time = time.time()

    for i, q in enumerate(questions, 1):
        question_text = q.get("Question", "").strip().strip('"')
        category = q.get("Category", "").strip()
        cluster_level = q.get("Cluster_Level", "").strip()
        topic = q.get("Topic", "").strip()
        expected_source = q.get("Expected_Source", "").strip()
        expected_answer = q.get("Expected_Answer", "").strip().strip('"')
        failure_type = q.get("Failure_Type", "").strip()

        print(f"[{i:03d}/{total}] [{category}] {question_text[:68]}...")

        for stat_dict, key in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
            if key not in stat_dict:
                stat_dict[key] = {"pass": 0, "partial": 0, "fail": 0, "total": 0}
            stat_dict[key]["total"] += 1

        payload = {"question": question_text}

        try:
            response = requests.post(api_url, json=payload, timeout=180)
            latency = response.elapsed.total_seconds()

            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")

                raw_sources = data.get("sources", [])
                sources = []
                source_matched = False
                for s in raw_sources:
                    if isinstance(s, dict):
                        url = s.get("url", "") or ""
                        title = s.get("title", "") or ""
                        section = s.get("section", "") or ""
                        src_str = url if url else f"{title} - {section}"
                        sources.append(src_str)
                        exp_clean = clean_url(expected_source)
                        if exp_clean and (
                            exp_clean in clean_url(url)
                            or exp_clean in clean_url(title)
                            or exp_clean in clean_url(section)
                        ):
                            source_matched = True
                    elif isinstance(s, str):
                        sources.append(s.strip())
                        exp_clean = clean_url(expected_source)
                        if exp_clean and exp_clean in clean_url(s):
                            source_matched = True

                quality = check_answer_quality(answer, expected_answer)

                if source_matched and quality == "PASS":
                    status = "PASS"; passed += 1
                    for d, k in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
                        d[k]["pass"] += 1
                    icon = "[PASS]"
                elif quality == "PARTIAL" or (source_matched and quality != "FAIL"):
                    status = "PARTIAL"; partial += 1
                    for d, k in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
                        d[k]["partial"] += 1
                    icon = "[PART]"
                else:
                    status = "FAIL"; failed += 1
                    for d, k in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
                        d[k]["fail"] += 1
                    icon = "[FAIL]"

                print(f"    {icon} latency={latency:.2f}s | src={source_matched} | q={quality}")

                results.append({
                    "q_num": i, "question": question_text,
                    "category": category, "cluster_level": cluster_level,
                    "topic": topic, "failure_type": failure_type,
                    "expected_source": expected_source, "expected_answer": expected_answer,
                    "actual_answer": answer, "actual_sources": sources,
                    "source_matched": source_matched, "quality": quality,
                    "latency_sec": round(latency, 3), "status": status, "error": None,
                })

            else:
                print(f"    [FAIL] HTTP {response.status_code}")
                failed += 1
                for d, k in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
                    d[k]["fail"] += 1
                results.append({
                    "q_num": i, "question": question_text,
                    "category": category, "cluster_level": cluster_level,
                    "topic": topic, "failure_type": failure_type,
                    "expected_source": expected_source, "expected_answer": expected_answer,
                    "actual_answer": "", "actual_sources": [],
                    "source_matched": False, "quality": "FAIL",
                    "latency_sec": 0.0, "status": "FAIL",
                    "error": f"HTTP {response.status_code}",
                })

        except Exception as e:
            print(f"    [FAIL] Exception: {e}")
            failed += 1
            for d, k in [(cat_stats, category), (level_stats, cluster_level), (topic_stats, topic)]:
                d[k]["fail"] += 1
            results.append({
                "q_num": i, "question": question_text,
                "category": category, "cluster_level": cluster_level,
                "topic": topic, "failure_type": failure_type,
                "expected_source": expected_source, "expected_answer": expected_answer,
                "actual_answer": "", "actual_sources": [],
                "source_matched": False, "quality": "FAIL",
                "latency_sec": 0.0, "status": "FAIL",
                "error": str(e),
            })

        time.sleep(1.5)  # rate-limit buffer

    # ── Summary ────────────────────────────────────────────────────────────────
    total_time = time.time() - start_time
    latencies = [r["latency_sec"] for r in results if r["latency_sec"] > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    pass_rate = (passed / total) * 100 if total else 0.0
    partial_rate = (partial / total) * 100 if total else 0.0

    output = {
        "meta": {
            "tester": "Dhruvam",
            "domain": "faculty/cluster",
            "cluster_image": "faculty_cluster_diagram.jpeg",
            "started_at": start_ts,
            "finished_at": datetime.now().isoformat(),
        },
        "summary": {
            "total": total, "passed": passed, "partial": partial, "failed": failed,
            "pass_rate_pct": round(pass_rate, 1),
            "partial_rate_pct": round(partial_rate, 1),
            "avg_latency_sec": round(avg_latency, 3),
            "total_time_sec": round(total_time, 1),
        },
        "by_category": cat_stats,
        "by_cluster_level": level_stats,
        "by_topic": topic_stats,
        "results": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*65}")
    print(f" EVALUATION COMPLETE")
    print(f"{'='*65}")
    print(f" Total:        {total}")
    print(f" PASS:         {passed} ({pass_rate:.1f}%)")
    print(f" PARTIAL:      {partial} ({partial_rate:.1f}%)")
    print(f" FAIL:         {failed} ({(failed/total*100):.1f}%)")
    print(f" Avg Latency:  {avg_latency:.3f}s")
    print(f" Total Time:   {total_time:.1f}s")
    print(f"\n Per-level breakdown:")
    for lv, st in sorted(level_stats.items()):
        print(f"   {lv}: PASS={st['pass']} PARTIAL={st['partial']} FAIL={st['fail']}")
    print(f"\n Results saved -> {output_path}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA Cluster Evaluation")
    parser.add_argument("--api-url", default="http://127.0.0.1:8007/chat")
    parser.add_argument("--csv", default="eval/cluster_questions.csv")
    parser.add_argument("--output", default="eval/cluster_results.json")
    args = parser.parse_args()
    run_evaluation(args.api_url, args.csv, args.output)
