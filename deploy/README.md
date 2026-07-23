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
│ NODE 2: vLLM NODE 1 (GPU)         │      │ NODE 3: vLLM NODE 2 (GPU)         │      │ NODE 4: RETRIEVAL & INFRASTRUCTURE NODE       │
│                                   │      │                                   │      │                                               │
│  ┌─────────────────────────────┐  │      │  ┌─────────────────────────────┐  │      │  ┌──────────────┐       ┌──────────────────┐  │
│  │ vLLM Engine (Qwen3-32B)     │  │      │  │ vLLM Engine (Qwen3-32B)     │  │      │  │ Qdrant Vector│       │ Embedding Service│  │
│  │ OpenAI API (:8000)          │  │      │  │ OpenAI API (:8000)          │  │      │  │ DB (:6333)   │       │ TEI / FastEmbed  │  │
│  └─────────────────────────────┘  │      │  └─────────────────────────────┘  │      │  └──────────────┘       └────────┬─────────┘  │
└───────────────────────────────────┘      └───────────────────────────────────┘      │                                  │            │
                                                                                      │  ┌──────────────┐       ┌────────▼─────────┐  │
                                                                                      │  │  Prometheus  │       │ Reranker Service │  │
                                                                                      │  │   (:9090)    │       │ TEI / BGE-v2     │  │
                                                                                      │  └──────┬───────┘       └──────────────────┘  │
                                                                                      │         │                                     │
                                                                                      │  ┌──────▼───────┐                             │
                                                                                      │  │   Grafana    │                             │
                                                                                      │  │   (:3000)    │                             │
                                                                                      │  └──────────────┘                             │
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
├── node4/                     # Node 4: Search Engine (Qdrant, Embedding/Reranker) + Monitoring (Prometheus, Grafana)
│   ├── docker-compose.yml
│   └── .env.node4.example
├── nginx/                     # Reverse Proxy & SSL Configuration
│   └── nginx.conf
├── scripts/                   # CD helpers (app-only deploy + Actions runner install)
│   ├── deploy-apps.sh
│   └── install-actions-runner.sh
└── monitoring/                # Prometheus & Grafana Monitoring Configuration
    ├── prometheus.yml
    └── grafana-datasource.yml
```

---

## Quick Start Deployment Guide

### Node 4: Search Engine & Monitoring Stack (Start First)
On **Node 4**:
```bash
cd deploy/node4
cp .env.node4.example .env
# Edit .env and update Prometheus scrape targets in ../monitoring/prometheus.yml with actual LAN IPs!
docker compose up -d --build
```
*Exposes:* Qdrant on `:6333`, Embedding/Reranker service on `:8001`, Prometheus on `:9090`, and Grafana on `:3000`.

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

### 2. What CD runs

Workflow: [`.github/workflows/cd-auto-deploy.yml`](../.github/workflows/cd-auto-deploy.yml)

| Triggers | Action |
|----------|--------|
| `workflow_dispatch` (manual) | Deploy chosen ref |
| `push` to `main` touching `aura/**`, `server/**`, `deploy/node1/**`, … | Auto-deploy |

Script: [`deploy/scripts/deploy-apps.sh`](scripts/deploy-apps.sh)

```bash
# Equivalent manual deploy on Node 1
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

On **Node 4**:
```bash
# Verify Prometheus Scrape Targets
curl -fsS http://localhost:9090/-/healthy

# Verify Grafana
curl -fsS http://localhost:3000/api/health
```
