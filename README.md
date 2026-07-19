<div align="center">
  <img width="250" alt="AURA_Logo" src="https://github.com/user-attachments/assets/591dad76-42ae-473b-ab30-be8c951bbc07" />

  <h1> AURA</h1>
  <h2>AI-powered University Resource Assistant</h2>
  
  <p>
    <a href="#architecture-overview"><img src="https://img.shields.io/badge/Agentic_RAG-LangGraph-0A66C2?style=for-the-badge&logo=openai&logoColor=white" alt="Agentic RAG" /></a>
    <a href="#architecture-overview"><img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" /></a>
    <a href="#getting-started"><img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" /></a>
    <img src="https://img.shields.io/badge/vLLM-NVIDIA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="NVIDIA GPU" />
  </p>

  <p align="center">
    <b>An advanced Agentic Retrieval-Augmented Generation (RAG) system</b><br/> 
    Designed to intelligently answer students' and faculty members' questions using the university's curated knowledge base.
  </p>
  
  <p>
    <a href="https://www.notion.so/Dhirubhai-Ambani-University-PWA-Checklist-36d37054896680329226c5b61049b176"><strong>Explore the Project Board »</strong></a>
  </p>
</div>

---

## Architecture Overview

Unlike a conventional chatbot, **AURA** follows a sophisticated multi-stage reasoning pipeline:

- **FastAPI API Gateway:** Manages secure authentication (SSO) and request routing.
- **Agent Orchestrator (LangGraph):** The intelligence layer that plans execution and gathers information before querying the LLM.
- **Vector Retrieval & Reranking:** Uses **Qdrant** for semantic search and a **Cross-Encoder** for reranking to significantly improve accuracy.
- **Inference Layer:** Powered by **vLLM** on a dedicated **NVIDIA GPU cluster** for scalable, continuous-batching language generation.
- **Memory & Storage:** Contextual conversation memory via **Redis** and persistent analytics/logs via **PostgreSQL**.

> [!NOTE]  
> **Deployment:** All components are containerized and orchestrated using **Docker Compose** for high portability and linear scalability.

---

## Getting Started

### 1. Fork & Clone

Fork the repo on GitHub, then clone your fork:

```bash
git clone https://github.com/<your-username>/DAU-pwa.git
cd DAU-pwa
```

### 2. Add Upstream

Add the upstream remote so you can pull future changes:

```bash
git remote add upstream https://github.com/vaishcodescape/DAU-pwa.git
```

---

## Contribution Guidelines

We follow a strict Git workflow to keep our history clean and organized. All work happens on personal feature branches — **never** commit directly to `main` or `dev`.

### Branch Naming

| Pattern | Use for | Example |
|---------|---------|---------|
| ` <name>/<feature>` | New features | `aditya/auth-flow` |
| ` hotfix/<issue>` | Critical fixes straight to `main` | `hotfix/login-crash` |

**To start a new feature:**
```bash
git fetch upstream
git checkout -b <name>/<feature> upstream/dev
```

### Making Changes

Keep changes scoped to your feature. Each domain is owned by a sub-team — don't edit files outside your area without coordinating first.

| Domain | Owns |
|--------|------|
| **Frontend** | `src/app/`, `src/components/`, `src/hooks/`, `src/styles/` |
| **Backend / Infra** | `src/lib/api/`, `src/lib/db/`, server actions, CI/CD |
| **AI** | `src/lib/ai/`, prompt engineering, model evaluation |

### Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
# Examples
feat(auth): add OTP login via university email
fix(dashboard): correct timetable timezone offset
perf(ai): enable prompt caching on search handler
```

> [!TIP]  
> **Subject line must be 72 characters or fewer.** For `fix` commits, add a body explaining the root cause.

### Opening a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin <name>/<feature>
   ```
2. Open a PR on GitHub targeting the **`dev`** branch (not `main`).
3. Fill in the PR template: summary, test plan, and screenshots for any UI changes.
4. Link the related issue: `Closes #<issue-number>`.
5. Request a review. 

**Merging Requirements:**
- **1 approval** for `dev`
- **2 approvals** for `main` (leads only)

> [!WARNING]  
> PRs are **squash-merged** into `dev`. Direct pushes to `main` are blocked.

---

## Further Reading

Check out our detailed internal documentation:

- [`CLAUDE.md`](./CLAUDE.md) — Full coding rules and conventions
- [`AGENTS.md`](./AGENTS.md) — Guidelines for AI coding agents on this project

---

## License

[Apache 2.0](./LICENSE)
