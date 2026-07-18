# AURA frontend (Next.js) — Phase E (DO-4)
#
# Multi-stage build optimized for Next.js `output: "standalone"`:
#   1. deps    — install pnpm dependencies only (best layer-cache reuse)
#   2. builder — copy source, run `next build`
#   3. runner  — copy only the standalone server + static assets, run as a
#                non-root user. No pnpm, no dev deps, no source in the final
#                image.
#
# Build from the repo root:
#   docker build -f aura/Dockerfile -t aura-frontend ./aura

FROM node:22-alpine AS base
RUN corepack enable

# ---------------------------------------------------------------------------
FROM base AS deps
WORKDIR /app
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

# ---------------------------------------------------------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# BACKEND_URL is only read at request-time by the route handlers, but Next
# still needs *some* value present at build time for env validation.
ENV NEXT_TELEMETRY_DISABLED=1
RUN pnpm build

# ---------------------------------------------------------------------------
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
