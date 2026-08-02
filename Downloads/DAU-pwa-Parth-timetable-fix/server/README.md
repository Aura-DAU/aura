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

## Production hardening checklist

Set `ENV=production` (or `AURA_ENV=production`). Startup fails if required secrets are missing.

| Variable | Purpose |
|----------|---------|
| `PROD_FRONTEND_ORIGIN` | CORS allowlist for the Next.js origin (required in production) |
| `INTERNAL_JWT_SECRET` | Shared HS256 secret with Next.js (≥256-bit) |
| `INTERNAL_RESOLVE_SECRET` | Header secret for `/internal/resolve-identity` |
| `ECAMPUS_VAULT_KEY` | Fernet key for eCampus credential vault (required when `ERP_DB_HOST` unset) |
| `REDIS_URL` | Shared question quota across workers (falls back to in-memory if unset) |
| `INTERNAL_RESOLVE_ALLOWLIST` | Optional comma-separated IPs/CIDRs allowed to call `/internal/*` |

**Network isolation:** Do not expose FastAPI `/internal/*` to the public internet. Prefer binding the API to a private network/VPC and only allow the Next.js BFF. Use `INTERNAL_RESOLVE_ALLOWLIST` as defense-in-depth when the API is reachable from more than one host.

**eCampus vault:** Store `ECAMPUS_VAULT_DB` on a dedicated volume; the process sets file mode `0600` when possible. Never log plaintext passwords.

## Tests

```bash
cd server/rag
pytest pipeline/tests
```

See [rag/README.md](rag/README.md) for RAG-specific notes. Database schema overview: [docs/database_schema.md](docs/database_schema.md).
