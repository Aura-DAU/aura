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

## Health Checks & Verification

On **Node 1**:
```bash
# Verify Gateway Health
curl -fsS https://localhost/backend/health

# Check logs to confirm multi-node connections
docker compose -f deploy/node1/docker-compose.yml logs backend | grep "InferenceRouter"
```
