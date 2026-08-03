# DAU PWA Live Chatbot Test Report

- Run time: 2026-08-03 18:14:46 India Standard Time
- Target: live Node 1 HTTPS deployment
- Health: HTTP 200, `{"status":"online","service":"AURA API"}`
- Mode: website guest path via `/api/chat`
- Scope requested: Academics & Curriculum (~60), Course Policies (~50)
- Scope executed in this run: 10 guest smoke questions because anonymous website quota is 10/day

## Summary

- PASS: 0
- REVIEW: 10
- FAIL: 0
- BLOCKED: 0

All 10 live website requests returned HTTP 200, but every answer returned the generic backend generation error:

```text
Sorry, I encountered an error while generating a response. Please try again.
```

## Where it goes wrong

The live vLLM APIs expose the served model id `aura-llm` from `/v1/models`.
The deployment/backend defaults were still using the HuggingFace model path `Qwen/Qwen3-32B-AWQ` as the request model id in several places.

That creates this failure path:

1. Website sends the user question to `/api/chat`.
2. Backend reaches retrieval/generation.
3. Backend asks the OpenAI-compatible vLLM API for model `Qwen/Qwen3-32B-AWQ`.
4. Live vLLM only serves `aura-llm`.
5. Generation fails and the website shows the generic error response.

Fix applied in this branch: `VLLM_MODEL` now means the served model id (`aura-llm`), and `VLLM_MODEL_PATH` means the model weights path used when starting vLLM (`Qwen/Qwen3-32B-AWQ`).

## Results

| # | Category | Verdict | HTTP | Time | Question | Missing / Notes |
|---:|---|---|---:|---:|---|---|
| 1 | Academics & Curriculum | REVIEW | 200 | 27.78s | What undergraduate programmes are offered at DAU? | programme, B.Tech, Data period:, citations/sources |
| 2 | Academics & Curriculum | REVIEW | 200 | 32.31s | What is the curriculum structure for B.Tech ICT? | ICT, curriculum, Data period:, citations/sources |
| 3 | Academics & Curriculum | REVIEW | 200 | 41.86s | Which courses are listed for the first year B.Tech curriculum? | course, Data period:, citations/sources |
| 4 | Academics & Curriculum | REVIEW | 200 | 32.21s | What are the credit requirements for B.Tech ICT? | credit, Data period:, citations/sources |
| 5 | Academics & Curriculum | REVIEW | 200 | 26.76s | What electives are available in the Computational Science area? | elective, Computational, Data period:, citations/sources |
| 6 | Course Policies | REVIEW | 200 | 4.20s | What is the attendance policy for DAU courses? | attendance, Data period:, citations/sources |
| 7 | Course Policies | REVIEW | 200 | 4.42s | How is course grading handled at DAU? | grading, Data period:, citations/sources |
| 8 | Course Policies | REVIEW | 200 | 4.57s | What are course outcomes and where are they mentioned in course policy documents? | outcome, Data period:, citations/sources |
| 9 | Course Policies | REVIEW | 200 | 31.27s | What syllabus modules are listed for Introduction to ICT? | module, ICT, Data period:, citations/sources |
| 10 | Course Policies | REVIEW | 200 | 27.95s | What does a DAU course policy usually include? | policy, Data period:, citations/sources |

## Live endpoint checks

- Node 1 HTTPS health route: HTTP 200
- Node 1 backend health route: HTTP 200
- vLLM node 1 `/v1/models`: served model `aura-llm`
- vLLM node 2 `/v1/models`: served model `aura-llm`
- vLLM node 3 `/v1/models`: served model `aura-llm`
- Qdrant collections route: reachable, collection `aura_documents`

## Blocker for full 110-question website run

The public website guest route is intentionally limited to 10 questions/day.
To run all ~110 questions through the deployed website, use either:

- a signed-in DAU browser session, or
- an explicitly approved dedicated server-side test identity.
