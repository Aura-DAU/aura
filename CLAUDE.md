# DAU PWA — Claude Code Ruleset

Progressive Web App for Dhirubhai Ambani University, enriched with AI.
Team lead: Aditya Vaish and Vedant Shah. Domain-based teams, 10–20 developers.

---

## Stack

| Layer | Choice |
|-------|--------|
| Framework | Next.js (App Router) |
| Language | TypeScript (strict) |
| UI components | shadcn/ui |
| Styling | Tailwind CSS v4 |
| Package manager | pnpm |
| Backend / DB | TBD — keep data-layer code behind an adapter interface |
| PWA | next-pwa or Serwist |
| AI features | Anthropic SDK (claude-sonnet-4-6 default) |

---

## Repository Layout

```
src/
  app/              # Next.js App Router pages and layouts
  components/
    ui/             # shadcn/ui primitives (do not hand-edit)
    common/         # Shared layout and utility components
    features/       # Feature-scoped components (owned by a sub-team)
  lib/
    api/            # Typed API clients and server actions
    db/             # Data-layer adapters (backend-agnostic interfaces)
    ai/             # AI helpers and prompt templates
    utils/          # Pure utility functions, no side effects
  hooks/            # Custom React hooks
  styles/           # Global CSS and Tailwind base layers
  types/            # Shared TypeScript types and Zod schemas
public/
  icons/            # PWA icon set (all sizes)
  manifest.webmanifest
```

---

## Coding Rules

### Scope Isolation (Critical for Team Work)

Each developer works on their own feature branch. Claude must **only modify files directly required by the current task**. It must not:

- Refactor, reformat, or "improve" code it wasn't asked to touch.
- Edit files owned by another sub-team without explicit confirmation.
- Add new abstractions, helpers, or shared utilities unless the task explicitly calls for them.
- Change shared config files (`tailwind.config.ts`, `next.config.ts`, `tsconfig.json`, `package.json`) without asking first.

When Claude is unsure whether a file is in scope, it must ask — not assume and edit.

See `AGENTS.md` for the full agent behaviour ruleset.

### General

- TypeScript strict mode is non-negotiable. No `any`, no `@ts-ignore`.
- Every public function and component must be typed. Infer return types where obvious; annotate where they cross module boundaries.
- Do not add comments explaining *what* code does. Add one if the *why* is non-obvious (hidden constraint, spec quirk, workaround).
- No dead code committed. Remove unused imports, variables, and branches.
- Keep files under 300 lines. Split by responsibility, not by length.

### React / Next.js

- Use Server Components by default. Add `"use client"` only when you need browser APIs or interactivity.
- Data fetching lives in Server Components or server actions — never `useEffect` + `fetch`.
- Server actions go in `lib/api/` with a `.action.ts` suffix. They must be `async` and validated with Zod before touching any data layer.
- Route handlers (`route.ts`) are for webhooks and external integrations only.
- `loading.tsx` and `error.tsx` must exist for every route segment that fetches data.
- Never put business logic inside page components. Pages compose; `lib/` computes.

### Components

- One component per file. Filename matches the exported component name (PascalCase).
- shadcn/ui components in `components/ui/` are generated — never edit them directly. Customise via Tailwind variants or a wrapper in `components/common/`.
- Feature components belong in `components/features/<feature-name>/` and are owned by one sub-team.
- Props interfaces are defined above the component in the same file, not in a separate types file.
- Avoid prop-drilling beyond two levels. Use React Context or a lightweight state store.

### Styling

- Tailwind utility classes only. No inline `style={{}}` props except for truly dynamic values (e.g. calculated widths).
- Use `cn()` from `lib/utils.ts` for conditional class merging.
- Responsive design is mobile-first. Base styles target mobile; use `md:`, `lg:` for larger viewports.
- Colour tokens come from `tailwind.config.ts` — do not hardcode hex values.

### AI Integration

- All Anthropic SDK calls go through `lib/ai/`. No direct `anthropic.messages.create()` calls in components or pages.
- Default model: `claude-sonnet-4-6`. Override at call-site only when justified.
- Every AI call must include structured error handling — the AI layer should never crash the user's session.
- Prompt templates live in `lib/ai/prompts/` as exported `const` strings or builder functions, not inline strings.
- Enable prompt caching (`cache_control`) on any prompt that exceeds 1 024 tokens.

### PWA

- The service worker must not cache API responses by default — opt-in only for read-only, low-sensitivity endpoints.
- `manifest.webmanifest` must stay valid at all times (`pnpm run check:pwa`).
- All user-facing pages must be accessible offline with a meaningful fallback.

### Security

- Never commit secrets. `.env.local` is gitignored — use `.env.example` for shape.
- All user input that reaches a server action or API must be validated with Zod at the boundary.
- Use `next/headers` cookies API for session tokens — never localStorage for auth state.
- Escape all user-generated content rendered as HTML; prefer React's default escaping over `dangerouslySetInnerHTML`.
- Run `pnpm audit` before any PR that adds or upgrades dependencies.

---

## Git Workflow

### Branches

| Pattern | Purpose |
|---------|---------|
| `main` | Production-ready, protected. No direct pushes. |
| `dev` | Integration branch. All PRs target `dev`. |
| `<name>/<feature>` | Personal feature branches (e.g. `aditya/auth-flow`) |
| `hotfix/<issue>` | Critical fixes that go directly to `main` via fast PR |

### Commits

Follow Conventional Commits:

```
<type>(<scope>): <short description>

Types: feat, fix, chore, refactor, docs, test, style, perf, ci
Scope: auth, dashboard, ai, pwa, ui, infra, ...

Examples:
  feat(auth): add OTP login via university email
  fix(dashboard): correct timetable timezone offset
  perf(ai): enable prompt caching on search handler
```

- Subject line ≤ 72 characters.
- Body optional, but required for `fix` commits — explain the root cause.
- No "WIP" commits on `dev` or `main`.

### Pull Requests

- PR title mirrors the commit format.
- Fill the PR template: summary, test plan, screenshots for UI changes.
- Minimum 1 review approval before merge to `dev`; 2 for `main`.
- Squash-merge feature branches into `dev`. Merge commits for `dev` → `main`.
- Link the related GitHub issue (`Closes #<n>`).

---

## Sub-team Ownership

| Domain | Owns |
|--------|------|
| Frontend | `src/app/`, `src/components/`, `src/hooks/`, `src/styles/` |
| Backend / Infra | `src/lib/api/`, `src/lib/db/`, server actions, CI/CD |
| AI | `src/lib/ai/`, prompt engineering, model evaluation |

Cross-domain changes require a review from the owning team.

---

## Commands

```bash
pnpm dev          # Start dev server (localhost:3000)
pnpm build        # Production build
pnpm lint         # ESLint + Prettier check
pnpm lint:fix     # Auto-fix lint issues
pnpm type-check   # tsc --noEmit
pnpm test         # Vitest unit tests
pnpm test:e2e     # Playwright end-to-end
pnpm check:pwa    # Validate manifest and service worker
pnpm audit        # Check for vulnerable dependencies
```

Run `pnpm lint` and `pnpm type-check` before every commit.

---

## Environment Variables

Copy `.env.example` to `.env.local` and fill in values. Never commit `.env.local`.

Required variables are documented in `.env.example` with inline comments.

---

## Testing

- Unit tests live alongside source: `<module>.test.ts`.
- E2E tests live in `e2e/` and use Playwright.
- Every server action must have at least one unit test covering the happy path and one covering invalid input.
- AI features: mock the Anthropic client in unit tests; use real calls only in a dedicated integration test suite.
- Aim for meaningful coverage, not 100% line coverage. Untested business logic is a bug waiting to happen.

---

## Accessibility

- All interactive elements must be keyboard-navigable.
- Every image needs an `alt` attribute (empty string for decorative images).
- Use semantic HTML elements. Do not replace `<button>` with `<div onClick>`.
- Run `pnpm lint` — the ESLint accessibility plugin (`eslint-plugin-jsx-a11y`) is enabled.

---

## When You Are Unsure

1. Check this file and `AGENTS.md` first.
2. Check existing patterns in the codebase (`src/lib/`, `src/components/`).
3. Ask in the team Discord / GitHub Discussion before inventing a new pattern.
4. Open a draft PR early if your change affects more than one domain.
