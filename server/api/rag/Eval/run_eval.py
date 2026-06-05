#!/usr/bin/env python3
import csv
import json
import argparse
import requests
import time
from typing import List, Dict, Any

def run_evaluation(api_url: str, csv_path: str, output_path: str) -> None:
    print(f"Starting evaluation using dataset: {csv_path}")
    print(f"Target API Endpoint: {api_url}")
    
    questions: List[Dict[str, str]] = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            questions.append(row)
            
    total = len(questions)
    passed = 0
    failed = 0
    results: List[Dict[str, Any]] = []
    
    start_time = time.time()
    
    for i, q in enumerate(questions, 1):
        question_text = q.get("Question", "")
        category = q.get("Category", "")
        expected_source = q.get("Expected Source", "").strip()
        expected_answer = q.get("Expected Answer", "").strip()
        
        print(f"[{i}/{total}] Testing: {question_text[:50]}...")
        
        payload = {"question": question_text}
        
        try:
            # Call the local RAG API
            response = requests.post(api_url, json=payload, timeout=15)
            latency = response.elapsed.total_seconds()
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer", "")
                
                # Support both list of strings and list of dicts for sources
                raw_sources = data.get("sources", [])
                sources = []
                source_matched = False
                
                for s in raw_sources:
                    if isinstance(s, dict):
                        url = s.get("url", "") or ""
                        title = s.get("title", "") or ""
                        section = s.get("section", "") or ""
                        sources.append(url if url else f"{title} - {section}")
                        
                        exp_lower = expected_source.lower()
                        if exp_lower in url.lower() or exp_lower in title.lower() or exp_lower in section.lower():
                            source_matched = True
                    elif isinstance(s, str):
                        sources.append(s.strip())
                        if expected_source.lower() in s.lower():
                            source_matched = True
                
                # Basic check if answer contains text or is fallback
                is_valid_answer = len(answer.strip()) > 0
                
                if source_matched and is_valid_answer:
                    status = "PASS"
                    passed += 1
                else:
                    status = "FAIL"
                    failed += 1
                
                results.append({
                    "question": question_text,
                    "category": category,
                    "expected_source": expected_source,
                    "expected_answer": expected_answer,
                    "actual_answer": answer,
                    "actual_sources": sources,
                    "latency_sec": latency,
                    "status": status,
                    "error": None
                })
            else:
                print(f"  -> Error: Received status code {response.status_code}")
                failed += 1
                results.append({
                    "question": question_text,
                    "category": category,
                    "expected_source": expected_source,
                    "expected_answer": expected_answer,
                    "actual_answer": "",
                    "actual_sources": [],
                    "latency_sec": 0.0,
                    "status": "FAIL",
                    "error": f"HTTP status {response.status_code}"
                })
        except Exception as e:
            print(f"  -> Exception: {e}")
            failed += 1
            results.append({
                "question": question_text,
                "category": category,
                "expected_source": expected_source,
                "expected_answer": expected_answer,
                "actual_answer": "",
                "actual_sources": [],
                "latency_sec": 0.0,
                "status": "FAIL",
                "error": str(e)
            })
            
    total_time = time.time() - start_time
    accuracy = (passed / total) * 100 if total > 0 else 0.0
    avg_latency = sum(r["latency_sec"] for r in results) / len(results) if results else 0.0
    
    summary = {
        "metrics": {
            "total_questions": total,
            "passed": passed,
            "failed": failed,
            "accuracy_percent": round(accuracy, 2),
            "total_time_sec": round(total_time, 2),
            "avg_latency_sec": round(avg_latency, 3)
        },
        "results": results
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "="*40)
    print("EVALUATION COMPLETED SUCCESSFULLY")
    print("="*40)
    print(f"Total Questions: {total}")
    print(f"Passed:          {passed}")
    print(f"Failed:          {failed}")
    print(f"Accuracy:        {accuracy:.2f}%")
    print(f"Avg Latency:     {avg_latency:.3f} seconds")
    print(f"Results saved to: {output_path}")
    print("="*40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DAU RAG Evaluation Script")
    parser.add_argument("--api-url", default="http://localhost:3000/api/chat", help="RAG Chat API endpoint URL")
    parser.add_argument("--csv", default="server/api/rag/Eval/evaluation_dataset.csv", help="Path to evaluation dataset CSV")
    parser.add_argument("--output", default="server/api/rag/Eval/evaluation_results.json", help="Path to save output JSON")
    
    args = parser.parse_args()
    run_evaluation(args.api_url, args.csv, args.output)
