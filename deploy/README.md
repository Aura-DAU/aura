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

## Architecture

Matches the system-architecture doc's target design: self-hosted Qdrant for
the vector store, a self-hosted vLLM inference pool (`vllm-node1/2/3`,
routed by `pipeline/inference_router.py`'s least-loaded/failover logic),
and a LangGraph `StateGraph` (`pipeline/aura_chat_graph.py`) as the Agent
Orchestrator. The `vllm-node*` services need host GPUs and the NVIDIA
Container Toolkit — see the comments in `docker-compose.prod.yml` for
adjusting node count / GPU indices, or pointing `VLLM_ENDPOINTS` at
inference nodes running outside this compose file entirely.

Before first run, populate Qdrant from the existing markdown corpus:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend \
  bash -c "cd rag/pipeline/ingestion && python sync_db.py"
```

`pipeline/aura_chat.py` (the original hand-written control flow) and
`pipeline/key_manager.py` / `upload_to_pinecone.py` (the original
Groq/Pinecone code) are left in the repo, unused, as reference —
nothing currently imports them outside of each other.
