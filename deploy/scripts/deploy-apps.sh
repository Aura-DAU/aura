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
#   /opt/aura/app                  — git clone of DAU-pwa
#   /opt/aura/app/deploy/node1/.env  (preferred) OR /opt/aura/.env (legacy fallback)
#   /opt/aura/actions-runner       — self-hosted GitHub Actions runner
#
# Usage:
#   AURA_APP_ROOT=/opt/aura/app ./deploy/scripts/deploy-apps.sh
#   ./deploy/scripts/deploy-apps.sh main   # optional branch/ref (default: main)

set -euo pipefail

APP_ROOT="${AURA_APP_ROOT:-/opt/aura/app}"
COMPOSE_DIR="${APP_ROOT}/deploy/node1"
REF="${1:-main}"

# Resolve env file: explicit override, then node1 path, then legacy host path.
resolve_env_file() {
  local candidates=()
  if [[ -n "${AURA_ENV_FILE:-}" ]]; then
    candidates+=("${AURA_ENV_FILE}")
  fi
  candidates+=(
    "${APP_ROOT}/deploy/node1/.env"
    "/opt/aura/.env"
    "${APP_ROOT}/deploy/.env.prod"
  )
  local candidate
  for candidate in "${candidates[@]}"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

if [[ ! -d "${APP_ROOT}/.git" ]]; then
  echo "error: ${APP_ROOT} is not a git checkout" >&2
  exit 1
fi
if ! ENV_FILE="$(resolve_env_file)"; then
  echo "error: env file not found. Tried:" >&2
  echo "  \${AURA_ENV_FILE} (if set)" >&2
  echo "  ${APP_ROOT}/deploy/node1/.env" >&2
  echo "  /opt/aura/.env" >&2
  echo "  ${APP_ROOT}/deploy/.env.prod" >&2
  echo "On Node 1, create it once:" >&2
  echo "  cp ${APP_ROOT}/deploy/node1/.env.node1.example ${APP_ROOT}/deploy/node1/.env" >&2
  echo "  # or: ln -sfn /opt/aura/.env ${APP_ROOT}/deploy/node1/.env" >&2
  exit 1
fi
echo "==> Using env file: ${ENV_FILE}"
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
# Backend is not published on the host (security: no host :8000 bypass of nginx).
# Probe inside the container first, then via the public nginx edge if needed.
if command -v curl >/dev/null 2>&1; then
  docker compose --env-file "${ENV_FILE}" exec -T backend \
    curl -fsS --max-time 30 "http://127.0.0.1:8000/health" >/dev/null \
    || curl -fsS --max-time 30 -k "https://127.0.0.1/backend/health" >/dev/null \
    || {
      echo "warning: health endpoint not reachable yet; check: docker compose ps" >&2
      docker compose --env-file "${ENV_FILE}" ps aura backend nginx
      exit 1
    }
fi

echo "==> Deploy complete (vLLM / Postgres / Redis / Qdrant untouched)"
docker compose --env-file "${ENV_FILE}" ps aura backend nginx
