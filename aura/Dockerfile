# AURA frontend (Next.js) — Phase E (DO-4)
#
# Multi-stage build optimized for Next.js `output: "standalone"`:
#   1. deps    — install npm dependencies only (best layer-cache reuse)
#   2. builder — copy source, run `next build`
#   3. runner  — copy only the standalone server + static assets, run as a
#                non-root user. No package manager, no dev deps, no source in
#                the final image.
#
# Build from the repo root:
#   docker build -f aura/Dockerfile -t aura-frontend ./aura

FROM node:22-alpine AS base

# ---------------------------------------------------------------------------
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ---------------------------------------------------------------------------
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# BACKEND_URL is only read at request-time by the route handlers, but Next
# still needs *some* value present at build time for env validation.
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

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

# Chat history store (lib/db/chat-db.ts writes to $PWD/db). /app is root-owned,
# so the unprivileged runtime user cannot mkdir it on first write — create it
# up front owned by nextjs, otherwise every /api/auth/history POST 500s with
# EACCES. Mount a volume here in compose if history must survive redeploys.
RUN mkdir -p /app/db && chown nextjs:nodejs /app/db

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
