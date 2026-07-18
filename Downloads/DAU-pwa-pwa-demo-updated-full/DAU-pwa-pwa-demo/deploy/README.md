# AURA production deployment (Phase E)

Containerizes the two app services (`aura/` Next.js frontend, `server/`
FastAPI backend) behind an NGINX edge proxy, alongside Postgres and Redis.

## Layout
- `../aura/Dockerfile` — multi-stage Next.js standalone build
- `../server/Dockerfile` — FastAPI + Gunicorn/Uvicorn workers, FFmpeg installed
- `docker-compose.prod.yml` — wires the full stack together
- `nginx.conf` — edge reverse proxy / SSL termination
- `.env.prod.example` — required secrets (copy to `.env.prod`, fill in, never commit)

## Running it

```bash
cd deploy
cp .env.prod.example .env.prod   # fill in secrets
mkdir -p certs                   # drop fullchain.pem / privkey.pem here
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

The backend container mounts the repo's `data/` directory read-only at
`/app/data` — this backs the `/documents` endpoint that powers the citation
side-drawer (Phase C), and is also where you'd run ingestion scripts
(`server/rag/pipeline/ingestion/...`) ad hoc via `docker compose exec backend`.

## Known gap vs. the architecture doc

`AURA System Architecture and Working.pdf` describes a self-hosted Qdrant
vector store and on-prem vLLM/GPU inference nodes. This codebase currently
calls managed Pinecone and Groq's hosted API instead (see `server/rag/.env.example`),
so there's no local vector DB or inference-server process to containerize
yet. `docker-compose.prod.yml` has a commented `qdrant` service stub for
when that migration happens.
