#!/usr/bin/env bash
# Deploy Node 1 *application* containers only.
#
# Rebuilds/recreates: aura (Next.js) + backend (FastAPI/LangGraph) + nginx
# (nginx is recreated without --build so TLS/proxy config reloads if compose
# changed; image is not rebuilt).
#
# NEVER restarts: postgres, redis, or any remote Node 2/3/4 services
# (vLLM, Qdrant, TEI). Uses `docker compose ... --no-deps` so depends_on
# does not cascade into the databases.
#
# Expected layout on aura-node1:
#   /opt/aura/app          — git clone of DAU-pwa
#   /opt/aura/app/deploy/node1/.env
#   /opt/aura/actions-runner — self-hosted GitHub Actions runner
#
# Usage:
#   AURA_APP_ROOT=/opt/aura/app ./deploy/scripts/deploy-apps.sh
#   ./deploy/scripts/deploy-apps.sh main   # optional branch/ref (default: main)

set -euo pipefail

APP_ROOT="${AURA_APP_ROOT:-/opt/aura/app}"
ENV_FILE="${AURA_ENV_FILE:-${APP_ROOT}/deploy/node1/.env}"
COMPOSE_DIR="${APP_ROOT}/deploy/node1"
REF="${1:-main}"

if [[ ! -d "${APP_ROOT}/.git" ]]; then
  echo "error: ${APP_ROOT} is not a git checkout" >&2
  exit 1
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "error: env file not found: ${ENV_FILE}" >&2
  exit 1
fi
if [[ ! -f "${COMPOSE_DIR}/docker-compose.yml" ]]; then
  echo "error: compose file missing under ${COMPOSE_DIR}" >&2
  exit 1
fi

# Self-hosted runners have no interactive HTTPS credentials. Prefer either:
#   - GITHUB_TOKEN / GH_TOKEN in the environment (CD workflow), or
#   - SSH remote + read-only deploy key on the host (manual deploys).
git_with_auth() {
  if [[ -n "${GITHUB_TOKEN:-${GH_TOKEN:-}}" ]]; then
    local token="${GITHUB_TOKEN:-${GH_TOKEN}}"
    # Ephemeral — never writes the token into .git/config remotes.
    git -c "url.https://x-access-token:${token}@github.com/.insteadOf=https://github.com/" "$@"
  else
    git "$@"
  fi
}

echo "==> Updating ${APP_ROOT} to ${REF}"
cd "${APP_ROOT}"
git_with_auth fetch --prune origin
git checkout "${REF}"
git_with_auth pull --ff-only origin "${REF}"

echo "==> Rebuilding application services only (aura, backend)"
cd "${COMPOSE_DIR}"
# --no-deps: do not start/restart postgres or redis via depends_on
docker compose --env-file "${ENV_FILE}" up -d --build --no-deps --remove-orphans=false \
  aura \
  backend

echo "==> Refreshing nginx (no image build; no DB deps)"
docker compose --env-file "${ENV_FILE}" up -d --no-deps --no-build nginx

echo "==> Health check"
# Prefer internal backend health; fall back to compose ps if curl missing
if command -v curl >/dev/null 2>&1; then
  curl -fsS --max-time 30 "http://127.0.0.1:8000/health" >/dev/null \
    || curl -fsS --max-time 30 "https://127.0.0.1/backend/health" >/dev/null \
    || {
      echo "warning: health endpoint not reachable yet; check: docker compose ps" >&2
      docker compose --env-file "${ENV_FILE}" ps aura backend nginx
      exit 1
    }
fi

echo "==> Deploy complete (vLLM / Postgres / Redis / Qdrant untouched)"
docker compose --env-file "${ENV_FILE}" ps aura backend nginx
