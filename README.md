<img width="200" alt="AURA_Logo" src="https://github.com/user-attachments/assets/b8c42844-3d0c-4bc1-920f-3dedd9b731b5" />

<div align="center">
  <h1>AURA</h1>
  <h3>AI-powered University Resource Assistant</h3>
  
  <img src="https://img.shields.io/badge/Agentic_RAG-LangGraph-blue?style=for-the-badge&logo=openai" alt="Agentic RAG" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/vLLM-NVIDIA-76B900?style=for-the-badge&logo=nvidia" alt="NVIDIA GPU" />

  <p align="center">
    An advanced <b>Agentic Retrieval-Augmented Generation (RAG)</b> system designed to intelligently answer students' and faculty members' questions using the university's curated knowledge base.
  </p>
</div>

<hr />

## Architecture Overview

Unlike a conventional chatbot, **AURA** follows a sophisticated multi-stage reasoning pipeline:

*   **FastAPI API Gateway:** Manages secure authentication (SSO) and request routing.
*   **Agent Orchestrator (LangGraph):** The intelligence layer that plans execution and gathers information before querying the LLM.
*   **Vector Retrieval & Reranking:** Uses **Qdrant** for semantic search and a **Cross-Encoder** for reranking to significantly improve accuracy.
*   **Inference Layer:** Powered by **vLLM** on a dedicated **NVIDIA GPU cluster** for scalable, continuous-batching language generation.
*   **Memory & Storage:** Contextual conversation memory via **Redis** and persistent analytics/logs via **PostgreSQL**.

> **Deployment:** All components are containerized and orchestrated using **Docker Compose** for high portability and linear scalability.

**Project Status (Notion):** [Dhirubhai Ambani University PWA Checklist](https://www.notion.so/Dhirubhai-Ambani-University-PWA-Checklist-36d37054896680329226c5b61049b176)

---

## Getting Started

### 1. Fork & clone

Fork the repo on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-username>/DAU-pwa.git
cd DAU-pwa
```

Add the upstream remote so you can pull future changes:

```bash
git remote add upstream https://github.com/vaishcodescape/DAU-pwa.git
```

---

## Branch Naming

All work happens on personal feature branches — **never** commit directly to `main` or `dev`.

| Pattern | Use for |
|---------|---------|
| `<name>/<feature>` | New features (e.g. `aditya/auth-flow`) |
| `hotfix/<issue>` | Critical fixes that need to go straight to `main` |

Create your branch from the latest `dev`:

```bash
git fetch upstream
git checkout -b <name>/<feature> upstream/dev
```

---

## Making Changes

Keep changes scoped to your feature. Each domain is owned by a sub-team — don't edit files outside your area without coordinating first.

| Domain | Owns |
|--------|------|
| **Frontend** | `src/app/`, `src/components/`, `src/hooks/`, `src/styles/` |
| **Backend / Infra** | `src/lib/api/`, `src/lib/db/`, server actions, CI/CD |
| **AI** | `src/lib/ai/`, prompt engineering, model evaluation |

---

## Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
# Examples
feat(auth): add OTP login via university email
fix(dashboard): correct timetable timezone offset
perf(ai): enable prompt caching on search handler
```

> **Note:** Subject line must be 72 characters or fewer. For `fix` commits, add a body explaining the root cause.

---

## Opening a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin <name>/<feature>
   ```
2. Open a PR on GitHub targeting the **`dev`** branch (not `main`).
3. Fill in the PR template: summary, test plan, and screenshots for any UI changes.
4. Link the related issue: `Closes #<issue-number>`.
5. Request a review. Merging requires:
   *   **1 approval** for `dev`
   *   **2 approvals** for `main` (leads only)

> PRs are **squash-merged** into `dev`. Direct pushes to `main` are blocked.

---

## Further Reading

*   [`CLAUDE.md`](./CLAUDE.md) — full coding rules and conventions
*   [`AGENTS.md`](./AGENTS.md) — guidelines for AI coding agents on this project

---

## License

[Apache 2.0](./LICENSE)
