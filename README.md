# DAU PWA

A Progressive Web App for Dhirubhai Ambani University, enriched with AI.

> **Project Status (Notion):** https://www.notion.so/Dhirubhai-Ambani-University-PWA-Checklist-36d37054896680329226c5b61049b176

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

# 
## Branch Naming

All work happens on personal feature branches — never commit directly to `main` or `dev`.

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
| Frontend | `src/app/`, `src/components/`, `src/hooks/`, `src/styles/` |
| Backend / Infra | `src/lib/api/`, `src/lib/db/`, server actions, CI/CD |
| AI | `src/lib/ai/`, prompt engineering, model evaluation |

---

## Commit Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

# Examples
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

2. Open a PR on GitHub targeting the **`dev`** branch (not `main`).

3. Fill in the PR template: summary, test plan, and screenshots for any UI changes.

4. Link the related issue: `Closes #<issue-number>`.

5. Request a review. Merging requires:
   - **1 approval** for `dev`
   - **2 approvals** for `main` (leads only)

PRs are **squash-merged** into `dev`. Direct pushes to `main` are blocked.

---
    
## Further Reading

- [`CLAUDE.md`](./CLAUDE.md) — full coding rules and conventions
- [`AGENTS.md`](./AGENTS.md) — guidelines for AI coding agents on this project

---

## License

[Apache 2.0](./LICENSE)
