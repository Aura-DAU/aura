# AURA production deployment (Phase E)

Containerizes the monorepo apps (`aura/` Next.js, `server/` FastAPI + RAG)
behind an NGINX edge proxy, with Postgres, Redis, Qdrant, optional vLLM GPU
nodes, Prometheus, and Grafana.

## Layout

- `../aura/Dockerfile` — multi-stage Next.js standalone build
- `../server/Dockerfile` — FastAPI + Gunicorn/Uvicorn workers, FFmpeg
- `docker-compose.prod.yml` — full stack wiring
- `nginx.conf` — edge reverse proxy / SSL termination
- `.env.prod.example` — required secrets (copy to `.env.prod`, never commit)

## Architecture parity (vs system-architecture PDF)

| PDF service | Compose service | Notes |
|-------------|-----------------|--------|
| NGINX | `nginx` | TLS + rate limit + SSE-friendly chat proxy |
| FastAPI gateway | `backend` | Auth, routes, metrics |
| LangGraph orchestrator | *inside* `backend` | `AuraChatGraph` — not a separate container yet (Phase F) |
| Embedding / Cross-Encoder | *inside* `backend` | In-process torch models; set `RERANKER_DEVICE=cpu` unless backend has a GPU |
| Redis | `redis` | Quota / short-term memory |
| PostgreSQL | `postgres` | Auth + analytics |
| Qdrant | `qdrant` | Vector store |
| vLLM ×3 | `vllm-node1/2/3` | Compose profile `gpu` |
| Prometheus / Grafana | `prometheus` / `grafana` | Internal network only |
| (monorepo) Next.js PWA | `aura` | BFF + UI |

GPU addresses are **not** hardcoded in app code. Put them in `.env.prod` as
`VLLM_ENDPOINTS` (Compose DNS names or multi-host LAN IPs).

## Running it

```bash
cd deploy
cp .env.prod.example .env.prod   # fill in secrets
mkdir -p certs                   # drop fullchain.pem / privkey.pem here

# Validate the rendered compose file (no containers started)
docker compose -f docker-compose.prod.yml --env-file .env.prod config >/dev/null

# Core stack — no host GPUs required
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build

# With local vLLM nodes (needs NVIDIA Container Toolkit + GPUs)
docker compose -f docker-compose.prod.yml --env-file .env.prod --profile gpu up -d --build
```

### Inference endpoints (`VLLM_ENDPOINTS`)

Same-host Compose (default with `--profile gpu`):

```bash
VLLM_ENDPOINTS=http://vllm-node1:8000/v1,http://vllm-node2:8000/v1,http://vllm-node3:8000/v1
```

Multi-host GPU cluster (set reachable IPs/hostnames in `.env.prod`; you can
omit the compose `vllm-node*` services and only run vLLM on each GPU box):

```bash
VLLM_ENDPOINTS=http://10.0.0.11:8000/v1,http://10.0.0.12:8000/v1,http://10.0.0.13:8000/v1
```

Point Qdrant at another host the same way (`QDRANT_URL=http://10.0.0.14:6333`).
Compose may still start a local `qdrant` sidecar because of `depends_on`; traffic follows `QDRANT_URL`.

Single GPU:

```bash
VLLM_ENDPOINTS=http://vllm-node1:8000/v1
# start only node1, or point at any one OpenAI-compatible server
```

`InferenceRouter` (`server/rag/pipeline/inference_router.py`) picks the
least-loaded endpoint and fails over on retryable errors. LangGraph never
sees which GPU answered.

### Backend notes

The backend image is heavy: retrieval embeds + BGE reranker load in-process
alongside the LangGraph chat graph. Prefer `BACKEND_WORKERS=1` or `2` and
`RERANKER_DEVICE=cpu` unless the backend host itself has a GPU.

The backend container mounts the repo's `data/` directory read-only at
`/app/data` — this backs the `/documents` endpoint (citation side-drawer)
and ad-hoc ingestion via `docker compose exec backend`.

Before first run, populate Qdrant from the markdown corpus:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend \
  bash -c "cd rag/pipeline/ingestion && python sync_db.py"
```

## Verification

```bash
# Config must render without errors
docker compose -f docker-compose.prod.yml --env-file .env.prod config >/dev/null

# Backend health (via nginx path or compose network)
curl -fsS https://localhost/backend/health

# After --profile gpu (or external endpoints), backend logs should show:
#   [InferenceRouter] Initialized with N vLLM node(s): [...]
```

## Reference code left unused

`pipeline/aura_chat.py` (hand-written control flow) and
`pipeline/key_manager.py` / `upload_to_pinecone.py` (legacy Groq/Pinecone)
remain in the repo as reference — nothing currently imports them outside of
each other.
