# AGENTS.md — AI Agent Guidelines for DAU PWA

This file governs how Claude Code (and any other AI coding agents) should behave when assisting contributors on this project. All agents must read and follow both this file and `CLAUDE.md`.

---

## Core Principle: Minimal, Scoped Changes

**Agents must never touch code outside the scope of the current task.**

This is a large-scale team project. Every contributor owns a domain. An agent helping one developer must not silently modify, refactor, or "improve" files owned by another developer or unrelated to the current task.

When in doubt, do less. Ask the developer to confirm before touching a file that isn't obviously part of the task.

---

## What Agents Are Allowed to Do

- Edit files directly related to the task described by the developer.
- Create new files inside the correct domain directory.
- Run read-only shell commands (`pnpm lint`, `pnpm type-check`, `pnpm test`).
- Suggest (but not auto-apply) changes to shared config files (`tailwind.config.ts`, `tsconfig.json`, `next.config.ts`) — these affect the whole team.
- Read any file in the repo to understand context.

## What Agents Must NOT Do Without Explicit Confirmation

- Modify `src/components/ui/` (shadcn/ui generated files).
- Edit files in another sub-team's ownership area (see `CLAUDE.md` ownership table).
- Change shared configuration files (`tailwind.config.ts`, `tsconfig.json`, `next.config.ts`, `package.json`, `pnpm-lock.yaml`, CI workflows).
- Rename, move, or delete existing files.
- Add, upgrade, or remove npm packages.
- Refactor code that is not broken and not part of the stated task.
- Format or lint-fix files that the developer didn't ask to change.
- Push, merge, or create PRs autonomously.

If any of these actions are needed to complete the task, the agent must **stop and ask the developer** before proceeding.

---

## Scope Enforcement

Before writing any code, the agent must identify:

1. **The task scope**: What feature, bug, or file is the developer working on?
2. **The owning domain**: Frontend / Backend / AI?
3. **Files in scope**: Only files directly needed to complete the task.

If the agent realises it needs to touch a file outside the stated scope, it must surface this to the developer:

> "To complete this, I'd also need to change `src/lib/api/auth.action.ts`, which is in the Backend domain. Should I proceed, or would you prefer to coordinate with that team?"

---

## Branching Awareness

Agents should be aware of the current branch before making changes.

- If on `main` or `dev`: warn the developer and refuse to make changes. All work happens on personal feature branches (`<name>/<feature>`).
- If on a feature branch: proceed normally within scope.

---

## Code Quality Gates

Agents must ensure the following pass before reporting a task as done:

```bash
pnpm type-check   # zero TypeScript errors
pnpm lint         # zero ESLint errors
```

If tests exist for the modified module, the agent must also run:

```bash
pnpm test         # related tests pass
```

Do not report a task as complete if any of these fail.

---

## Commit Behaviour

Agents must not commit code unless the developer explicitly says "commit this" or "create a commit".

When asked to commit:
- Stage only files changed as part of the task.
- Follow the Conventional Commits format from `CLAUDE.md`.
- Never use `git add -A` or `git add .`.
- Never amend a previous commit — always create a new one.
- Never skip hooks (`--no-verify`).

---

## Handling Shared / Cross-Domain Files

Some files are touched by everyone and need special care:

| File | Rule |
|------|------|
| `src/types/*.ts` | Additive changes only. Never rename or remove exported types. |
| `src/lib/utils.ts` | Do not add feature-specific logic here. |
| `tailwind.config.ts` | Ask before changing. Affects all teams. |
| `next.config.ts` | Ask before changing. Affects build and routing. |
| `public/manifest.webmanifest` | Ask before changing. Owned by the Frontend team. |
| `.env.example` | Update when adding a new env variable. Never add secret values. |

---

## AI Feature Development

When working in `src/lib/ai/`:

- Every new AI capability must have a corresponding prompt file in `src/lib/ai/prompts/`.
- Do not use streaming unless the developer explicitly asks for it.
- Always include a fallback for when the AI call fails — the UI must degrade gracefully.
- Log token usage in development for cost tracking (`console.debug` in dev, structured log in prod).

---

## What Good Agent Output Looks Like

A high-quality agent response for this project:

1. Identifies the exact files it will change and explains why.
2. Makes the minimal change that satisfies the task.
3. Does not touch files outside the stated scope.
4. Runs `pnpm type-check` and `pnpm lint` and confirms they pass.
5. Summarises what changed in one or two sentences — no padding.

A bad agent response refactors surrounding code, "improves" unrelated files, adds abstractions the developer didn't ask for, or silently changes shared config.

---

## Escalation

If a task requires changes that cross domain boundaries, the agent should:

1. Explain what cross-domain change is needed and why.
2. Recommend the developer coordinate with the relevant sub-team.
3. Offer to draft the cross-domain change as a separate, clearly labelled PR.

Never merge cross-domain changes silently into a single feature PR.
