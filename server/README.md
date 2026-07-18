# AURA Backend Server

FastAPI gateway + RAG pipeline for the DAU AURA PWA.

## Layout

```
server/
  api/           # FastAPI app, auth, route modules
  db/            # Postgres connection + migrations
  rag/           # AURA RAG pipeline, eCampus, eval
  docs/          # Schema notes
  scripts/       # One-off validation helpers
```

## Setup

```bash
cd server/rag
cp .env.example .env   # fill AUTH_DB_URL, GROQ, Pinecone, JWT secrets
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
python db/migrate.py
```

## Run API

From `server/` (so `api` and `db` import cleanly; `rag` is also on the path):

```bash
uvicorn api.api:app --host 127.0.0.1 --port 8000 --reload
# equivalent: uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload
```

## Tests

```bash
cd server/rag
pytest pipeline/tests
```

See [rag/README.md](rag/README.md) for RAG-specific notes. Database schema overview: [docs/database_schema.md](docs/database_schema.md).
