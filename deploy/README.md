# AURA Production Multi-Node Deployment Topology

This directory contains the production deployment manifests for the **AURA Distributed Cluster** across 4 Ubuntu Nodes using Docker Compose.

---

## 4-Node Deployment Architecture

```
                               ┌───────────────────────────┐
                               │       USER CLIENTS        │
                               └─────────────┬─────────────┘
                                             │ HTTPS (:443)
┌────────────────────────────────────────────▼────────────────────────────────────────────┐
│ NODE 1: GATEWAY & ORCHESTRATION NODE (Ubuntu - CPU/RAM)                                 │
│                                                                                         │
│   ┌──────────────┐         ┌──────────────┐         ┌─────────────────┐                 │
│   │ NGINX Proxy  ├────────►│  AURA (PWA)  ├────────►│ FastAPI Gateway │                 │
│   │   (:80/443)  │         │   (:3000)    │         │     (:8000)     │                 │
│   └──────────────┘         └──────────────┘         └────────┬────────┘                 │
│                                                              │                          │
│   ┌──────────────┐         ┌──────────────┐                  │                          │
│   │  PostgreSQL  │         │    Redis     │         ┌────────▼────────┐                 │
│   │   (:5432)    │         │   (:6379)    │         │ LangGraph Engine│                 │
│   └──────────────┘         └──────────────┘         └────────┬────────┘                 │
└──────────────────────────────────────────────────────────────┼──────────────────────────┘
                                                               │
        ┌──────────────────────────────────────────────────────┼──────────────────────────────────────────────────────┐
        │ HTTP (Inference Router)                              │ HTTP (Vector & Rerank Client)                        │
        │                                                      │                                                      │
┌───────▼───────────────────────────┐      ┌───────────────────▼───────────────────────────┐      ┌────────────────────▼──────────────────────────┐
│ NODE 2: vLLM NODE 1 (GPU)         │      │ NODE 3: vLLM NODE 2 (GPU)         │      │ NODE 4: SEARCH & VECTOR ENGINE (GPU/CPU)      │
│                                   │      │                                   │      │                                               │
│  ┌─────────────────────────────┐  │      │  ┌─────────────────────────────┐  │      │  ┌──────────────┐       ┌──────────────────┐  │
│  │ vLLM Engine (Qwen3-32B)     │  │      │  │ vLLM Engine (Qwen3-32B)     │  │      │  │ Qdrant Vector│       │ Embedding Service│  │
│  │ OpenAI API (:8000)          │  │      │  │ OpenAI API (:8000)          │  │      │  │ DB (:6333)   │       │ TEI / FastEmbed  │  │
│  └─────────────────────────────┘  │      │  └─────────────────────────────┘  │      │  └──────────────┘       └────────┬─────────┘  │
└───────────────────────────────────┘      └───────────────────────────────────┘      │                                  │            │
                                                                                      │                         ┌────────▼─────────┐  │
                                                                                      │                         │ Reranker Service │  │
                                                                                      │                         │ TEI / BGE-v2     │  │
                                                                                      │                         └──────────────────┘  │
                                                                                      └───────────────────────────────────────────────┘
```

---

## Directory Layout

```
deploy/
├── node1/                     # Node 1: NGINX, Next.js (PWA), FastAPI + LangGraph, Postgres, Redis
│   ├── docker-compose.yml
│   └── .env.node1.example
├── node2/                     # Node 2: vLLM GPU Node 1
│   ├── docker-compose.yml
│   └── .env.node2.example
├── node3/                     # Node 3: vLLM GPU Node 2
│   ├── docker-compose.yml
│   └── .env.node3.example
├── node4/                     # Node 4: Qdrant & Embedding/Reranker Microservice
│   ├── docker-compose.yml
│   └── .env.node4.example
├── nginx/                     # Reverse Proxy & SSL Configuration
│   └── nginx.conf
├── scripts/                   # CD helpers (app-only deploy + Actions runner install)
│   ├── deploy-apps.sh
│   └── install-actions-runner.sh
└── monitoring/                # Prometheus & Grafana Monitoring
    ├── prometheus.yml
    └── grafana-datasource.yml
```

---

## Quick Start Deployment Guide

### Node 4: Search & Vector Engine (Start First)
On **Node 4**:
```bash
cd deploy/node4
cp .env.node4.example .env
docker compose up -d --build
```
*Exposes:* Qdrant on `:6333` and Embedding/Reranker service on `:8001`.

### Node 2 & Node 3: vLLM GPU Nodes
On **Node 2** (GPU Box 1):
```bash
cd deploy/node2
cp .env.node2.example .env
docker compose up -d
```
On **Node 3** (GPU Box 2):
```bash
cd deploy/node3
cp .env.node3.example .env
docker compose up -d
```
*Exposes:* OpenAI-compatible vLLM endpoints on port `:8000`.

### Node 1: Gateway & Orchestration Node
On **Node 1**:
```bash
cd deploy/node1
cp .env.node1.example .env
# Edit .env and replace <NODE_2_IP>, <NODE_3_IP>, <NODE_4_IP> with actual LAN IPs!
mkdir -p ../certs # add fullchain.pem / privkey.pem
docker compose up -d --build
```

---

## Auto-deploy (optional — Node 1 self-hosted runner)

For later CD: rebuild **only** `aura` + `backend` (+ refresh `nginx`) on every
qualified push. **Never** restarts Postgres, Redis, or remote vLLM / Qdrant.

### 1. Install the runner on Node 1

```bash
# On Node 1 — create dirs if needed
sudo mkdir -p /opt/aura/actions-runner /opt/aura/app
sudo chown -R "$USER:$USER" /opt/aura

# Clone once (if not already present)
git clone https://github.com/ossdaiict/DAU-pwa.git /opt/aura/app

# Node 1 compose env (required for CD) — pick one:
cp /opt/aura/app/deploy/node1/.env.node1.example /opt/aura/app/deploy/node1/.env
# edit /opt/aura/app/deploy/node1/.env
# OR if you already keep secrets at /opt/aura/.env:
# ln -sfn /opt/aura/.env /opt/aura/app/deploy/node1/.env

# Registration token: GitHub → Settings → Actions → Runners → New self-hosted runner
export RUNNER_TOKEN=...          # short-lived
export GITHUB_REPO_URL=https://github.com/ossdaiict/DAU-pwa
/opt/aura/app/deploy/scripts/install-actions-runner.sh

# Prefer a systemd service so the runner survives reboot
cd /opt/aura/actions-runner
sudo ./svc.sh install
sudo ./svc.sh start
```
*Exposes:* OpenAI-compatible vLLM endpoints on port `:8000`.

The runner must be registered with label **`aura-node1`** (the install script
sets this). The CD workflow targets:

```yaml
runs-on: [self-hosted, Linux, aura-node1]
```

### Git auth on Node 1 (required)

CD runs headless. An HTTPS clone with no credentials fails with:

```text
fatal: could not read Username for 'https://github.com': No such device or address
```

**CD path (recommended):** the workflow passes a token into `deploy-apps.sh`
via an ephemeral `url.*.insteadOf` rewrite (never written into
`/opt/aura/app/.git/config`).

1. Prefer a **repository secret** named `AURA_DEPLOY_GIT_TOKEN` (PAT with
   Contents: Read on this repo).  
   GitHub → Settings → Secrets and variables → Actions → New repository secret.
2. If that secret is unset, CD falls back to the job’s built-in `github.token`.

Never put PATs in workflow YAML, git remotes, or `deploy/node1/.env`. If a
token was pasted into chat or a ticket, **revoke it immediately** and create a
new one.

**Manual deploys:** either export a fine-scoped PAT as `GITHUB_TOKEN` for that
shell, or switch the checkout to SSH with a **read-only deploy key**:

```bash
# On Node 1 (once)
ssh-keygen -t ed25519 -f /opt/aura/.ssh/github_deploy -N ""
# Add /opt/aura/.ssh/github_deploy.pub as a Deploy key (read-only) on the repo
cd /opt/aura/app
git remote set-url origin git@github.com:ossdaiict/DAU-pwa.git
GIT_SSH_COMMAND="ssh -i /opt/aura/.ssh/github_deploy -o IdentitiesOnly=yes" \
  git fetch --prune origin
```

Do **not** put `GITHUB_TOKEN` / PATs / `RUNNER_TOKEN` in `deploy/node1/.env`.

### 2. What CD runs

Workflow: [`.github/workflows/cd-auto-deploy.yml`](../.github/workflows/cd-auto-deploy.yml)

| Triggers | Action |
|----------|--------|
| `workflow_dispatch` (manual) | Deploy chosen ref |
| `push` to `main` touching `aura/**`, `server/**`, `deploy/node1/**`, … | Auto-deploy |

Script: [`deploy/scripts/deploy-apps.sh`](scripts/deploy-apps.sh)

```bash
# Equivalent manual deploy on Node 1 (needs SSH deploy key or GITHUB_TOKEN)
/opt/aura/app/deploy/scripts/deploy-apps.sh main
```

Uses `docker compose up -d --build --no-deps aura backend` so database
containers are not touched.
## Health Checks & Verification

On **Node 1**:
```bash
# Verify Gateway Health
curl -fsS https://localhost/backend/health

# Check logs to confirm multi-node connections
docker compose -f deploy/node1/docker-compose.yml logs backend | grep "InferenceRouter"
```
