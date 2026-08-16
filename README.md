<div align="center">
    <img width="250" alt="AURA_Logo" src="https://github.com/user-attachments/assets/591dad76-42ae-473b-ab30-be8c951bbc07" />
   <h1>DAU PWA — AURA</h1>
   
   <h3> A Progressive Web App for <strong>Dhirubhai Ambani University</strong>, enriched with AI. </h3>
   
   <p>
       <a href="#architecture-overview"><img src="https://img.shields.io/badge/Agentic_RAG-LangGraph-0A66C2?style=for-the-badge&logo=openai&logoColor=white" alt="Agentic RAG" /></a>
       <a href="#architecture-overview"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
       <a href="#getting-started"><img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" /></a>
       <img src="https://img.shields.io/badge/vLLM-NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA GPU" />
     </p>
</div>

> [!IMPORTANT]
> This project is built by **GDG On Campus** and the **AI Club** of Dhirubhai Ambani University, under the supervision of **[Prof. Arpit Rana](https://www.linkedin.com/in/arpitrana/)**.

> [!WARNING]
> **A note for future GDG On Campus & AI Club members:** please take care of this project and keep it alive. Do not delete this file or the project — maintain it, hand it over cleanly to the next batch, and keep the ownership, setup, and contribution notes above up to date.
---

## Overview

DAU PWA (codename **AURA**) is a monorepo with two parts:

| Directory | What it is | Stack |
|-----------|------------|-------|
| [`aura/`](./aura) | The installable PWA frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, shadcn/ui, Serwist (service worker), NextAuth |
| [`server/`](./server) | API gateway + AI/RAG backend | FastAPI, PostgreSQL, RAG pipeline (Qdrant + HF) |

See [`server/README.md`](./server/README.md) for backend-specific setup.

---

## Architecture Overview

AURA is an agentic RAG system: the PWA talks to a FastAPI gateway, LangGraph orchestrates retrieval and inference, and GPU nodes serve the LLM.

```mermaid
graph TB
  U[Browser / PWA]

  subgraph gateway [Node 1 - Gateway]
    N[NGINX]
    A[AURA Next.js]
    B[FastAPI]
    L[LangGraph]
    PG[(PostgreSQL)]
    R[(Redis)]
  end

  subgraph gpu [Nodes 2 and 3 - vLLM]
    V2[vLLM Qwen3-32B]
    V3[vLLM Qwen3-32B]
  end

  subgraph retrieval [Node 4 - Retrieval]
    Q[(Qdrant)]
    E[Embedding]
    RR[Reranker]
  end

  U -->|HTTPS| N
  N --> A --> B --> L
  B --> PG
  B --> R
  L -->|InferenceRouter| V2
  L -->|InferenceRouter| V3
  L --> Q
  L --> E --> RR
```

Production multi-node layout, compose files, and CD: [`.github/deploy/README.md`](./.github/deploy/README.md).

---

## Getting Started

### Prerequisites

- **Node.js** 20+ and **npm** (frontend)
- **Python** 3.14+ (backend)

### 1. Fork & clone

Fork the repo on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-username>/DAU-pwa.git
cd DAU-pwa
```

Add the upstream remote so you can pull future changes:

```bash
git remote add upstream https://github.com/ossdaiict/DAU-pwa.git
```

### 2. Run the frontend

```bash
cd aura
npm install
cp .env.example .env.local   # fill in the documented values
npm dev                     # http://localhost:3000
```

### 3. Run the backend

```bash
cd server/rag
cp .env.example .env         # fill AUTH_DB_URL, GROQ, Pinecone, JWT secrets
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
python db/migrate.py
uvicorn api.api:app --host 127.0.0.1 --port 8000 --reload
```

---

## Branch Naming

All work happens on personal feature branches — **never commit directly to `main`**.


Create your branch from the latest `main`:

```bash
git fetch upstream
git checkout -b <name>/<feature> upstream/main
```

---

## Making Changes

Keep changes scoped to your feature. Each domain is owned by a sub-team — don't edit files outside your area without coordinating first.

| Domain | Owns |
|--------|------|
| Frontend | `aura/app/`, `aura/components/`, `aura/hooks/` |
| Backend / Infra | `server/api/`, `server/db/`, CI/CD |
| Agents | `server/rag/`, prompt engineering, model evaluation |

---

## Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

Examples:

```
feat(auth): add OTP login via university email
fix(dashboard): correct timetable timezone offset
perf(ai): enable prompt caching on search handler
```

Subject line must be 72 characters or fewer. For `fix` commits, add a body explaining the root cause.

---

## Opening a Pull Request

1. Push your branch to your fork:

   ```bash
   git push origin <name>/<feature>
   ```

2. Open a PR on GitHub targeting the **`main`** branch.

3. Fill in the PR template: summary, test plan, and screenshots for any UI changes.

4. Link the related issue: `Closes #<issue-number>`.

5. Request a review. Merging into `main` requires **at least 1 approval**.

PRs are **squash-merged** into `main`. Direct pushes to `main` are blocked.

---

## Further Reading

- [`CLAUDE.md`](./CLAUDE.md) — full coding rules and conventions
- [`AGENTS.md`](./AGENTS.md) — guidelines for AI coding agents on this project

---

## Credits

Built with ❤️ by **GDG On Campus** and the **AI Club** of Dhirubhai Ambani University, under the supervision of **[Prof. Arpit Rana](https://www.linkedin.com/in/arpitrana/)**.
