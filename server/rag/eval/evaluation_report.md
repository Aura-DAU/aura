# DAU PWA - Evaluation Report
This document summarizes the metrics of the evaluation dataset, outlines our testing methodology, and explains how to run benchmark testing once the RAG pipeline is fully active.

---

## 📊 Evaluation Dataset Summary

Our evaluation suite consists of **3,609 unique custom-curated questions** (with all semantic and syntax duplicates/overlaps removed) categorized into three major thematic areas representing large pools of test cases:

### Thematic Question Groups
1. **University Policies, Student Services & Careers (~1,500 Questions)**
   * *Actual Count:* **1,467 questions**
   * *Covers:* Scholarships (165), Placements & Careers (152), Policies (146), IT Services (142), Hostel (139), Student Services (138), Transportation (137), Internships (136), Campus Facilities (134), Library (133), and minor policies (45).
   
2. **Academic Programs, Curriculum & Admissions (~1,000 Questions)**
   * *Actual Count:* **1,068 questions**
   * *Covers:* Examinations (147), Graduation (144), Attendance (141), Admissions (140), Convocation (137), Program Info (135), Registration (126), Academic Regulations (41), Academics (27), and minor academic categories (30).

3. **General University Information, Faculty & Research (~1,000 Questions)**
   * *Actual Count:* **1,074 questions**
   * *Covers:* Faculty Profiles (457), Research & Projects (157), International Programs (128), Departments (95), About University (78), Infrastructure (33), Accreditation (13), Student Affairs & Clubs (31), Governance & Administration (29), and other minor categories (110).

---

## ⚙️ Benchmarking Framework & Execution

We have created an automated evaluation runner: [run_eval.py](file:///Users/vedant_shah/DAU-pwa/server/api/rag/Eval/run_eval.py).

### How to Run the Benchmark
Once the RAG API is running locally (e.g., on `http://localhost:3000/api/chat`), execute the following command:

```bash
python3 server/api/rag/Eval/run_eval.py --api-url http://localhost:3000/api/chat
```

### Script Output
* The script outputs a summary to the console and generates [evaluation_results.json](file:///Users/vedant_shah/DAU-pwa/server/api/rag/Eval/evaluation_results.json).
* The JSON results track exactly which questions passed or failed, the returned citations, and the latency in seconds.

---

## 🎯 Grading & Accuracy Criteria

An evaluation row is graded as a **PASS** if and only if both of the following conditions are met:
1. **Source Grounding (Recall):** The returned list of `sources` contains the `Expected Source` URL or file path specified in the CSV.
2. **Safe Answer Generation:** The answer is non-empty, coherent, and adheres to the citation rules (free from hallucinated links).

Source matching does not show whether the answer is right, so `run_eval.py` also scores the answer itself (`answer_quality.py`):

| Metric | How it is computed |
|---|---|
| `answer_correct` | Every number in `Expected Answer` appears in the answer, the answer is not an abstention, and token F1 ≥ 0.3 |
| Abstention | Rows whose `Expected Answer` is `NOT_FOUND` pass only if AURA says it could not find the information (`abstention_dataset.csv`) |
| `mean_consistency` | With `--repeat N`, mean pairwise word overlap of the N answers to the same question (1.0 = identical) |

Run against a signed-in API (the chat routes require a token) and gate on answer accuracy:

```bash
AURA_EVAL_TOKEN=<internal JWT> python3 server/rag/eval/run_eval.py \
  --csv server/rag/eval/representative_dataset.csv --repeat 3 --min-answer-accuracy 80
python3 server/rag/eval/run_eval.py --csv server/rag/eval/abstention_dataset.csv
```

Rows need a verified `Expected Answer` to be scored; rows without one only count toward source matching.

---

## ❌ Failure Classification Guidelines

When analyzing failures in the generated JSON report, categorize them into one of the following:

| Category | Description | Primary Cause | Remediation |
|---|---|---|---|
| **Retrieval Failure (Recall)** | The retriever failed to return the document containing the answer within Top-K. | Small chunk size, poor embedding matching, or low Top-K parameter. | Adjust chunk sizes, check embeddings, or increase Top-K value. |
| **Citation Mismatch** | The answer is correct, but the cited source list does not include the expected source. | Prompt engineering rules not enforcing source list generation in response metadata. | Update system prompt to strictly return cited sources array. |
| **Generation Failure** | The retriever found the document, but the LLM failed to extract the answer or returned a fallback message. | Strict prompt constraints or LLM reasoning failure. | Tune assistant guidelines or system prompt. |
| **Hallucination** | The LLM generated information not supported by the context or cited an external URL. | Insufficient grounding system prompts. | Enforce "strictly answer from context" rule in the system prompt. |

---

## 📝 Next Steps for Integration
1. **Teammate Integration:** Once Team 1 (Retrieval Pipeline) finishes the server actions/API endpoints, start the API server locally.
2. **Run Benchmark:** Run `run_eval.py` to generate the `evaluation_results.json` log.
3. **Analyze Results:** Fill in the final accuracy rate and update this report with target recommendations.
