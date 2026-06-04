# AURA RAG Backend — FastAPI

A standalone Python/FastAPI service that provides a production-grade Retrieval-Augmented Generation (RAG) pipeline for the AURA student assistant at Dhirubhai Ambani University.

---

## Architecture

```
POST /api/chat
  │
  ├─ 1. Semantic retrieval (sentence-transformers cosine similarity)
  │       └─ Indexes all .md files from /data at startup
  │
  ├─ 2. Grounded system prompt construction
  │
  ├─ 3. Anthropic Claude call (if ANTHROPIC_API_KEY is set)
  │
  └─ 4. Offline extractive fallback (if no API key)
```

---

## Setup

### Prerequisites
- Python 3.11+
- pip or a virtual environment manager (venv / conda)

### Install

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY if you want Claude responses
```

### Run

```bash
uvicorn app.main:app --reload --port 8000
```

The first startup takes a moment to download the embedding model and build the index.
Subsequent starts are fast (model is cached by sentence-transformers).

---

## API Reference

Interactive docs available at `http://localhost:8000/docs` when the server is running.

### `POST /api/chat`

**Request body:**
```json
{
  "message": "What is the hostel curfew timing?",
  "history": [
    { "role": "user", "content": "Hi AURA" },
    { "role": "assistant", "content": "Hello! How can I help you today?" }
  ],
  "student_profile": {
    "name": "Rahul Sharma",
    "branch": "B.Tech (ICT)",
    "year": "3rd Year",
    "semester": "Semester V",
    "interests": "AI, competitive coding"
  }
}
```

**Response:**
```json
{
  "success": true,
  "content": "According to the hostel rules, the curfew is 10 PM...",
  "citations": [
    { "title": "Hostel Rules (Student Services)", "file": "hostel_rules.md" }
  ]
}
```

### `GET /health`

Returns `{ "status": "ok", "service": "AURA RAG API" }`.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | `""` | Anthropic SDK key. If empty, offline mode activates. |
| `DATA_DIR` | `../../data` | Path to the directory with `.md` document subdirectories. |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence-Transformers model name. |
| `TOP_K` | `3` | Number of documents retrieved per query. |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins. |

---

## Wiring to the Next.js Frontend

Set `FASTAPI_RAG_URL=http://localhost:8000` in `pwa/dau-pwa/.env.local`.  
The Next.js `chat.action.ts` will proxy through `ragClient.ts` to this backend.
