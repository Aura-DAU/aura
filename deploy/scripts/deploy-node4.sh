#!/usr/bin/env bash
# Deploy Node 4 (search + monitoring) from Node 1 via SSH/rsync.
#
# Default (safe): sync deploy/ + services/, then recreate prometheus + grafana
# only — Qdrant and embedding-reranker are left running.
#
# Flags:
#   --dry-run       Print actions; rsync --dry-run; no compose changes
#   --with-search   Also rebuild/recreate embedding-reranker (not Qdrant)
#   --sync-only     rsync only; do not recreate any containers
#
# Required env:
#   AURA_NODE4_HOST   LAN IP or hostname of Node 4
#
# Optional env:
#   AURA_NODE4_SSH_USER   only if login ≠ AURA_SSH_USER (default aura)
#   AURA_APP_ROOT / AURA_REMOTE_APP_ROOT / AURA_SSH_USER / AURA_SSH_KEY
#
# Usage (on Node 1):
#   AURA_NODE4_HOST=10.x.x.4 AURA_NODE4_SSH_USER=aura4 ./deploy/scripts/deploy-node4.sh
#   ./deploy/scripts/deploy-node4.sh --dry-run
#   ./deploy/scripts/deploy-node4.sh --with-search

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/remote.sh
source "${SCRIPT_DIR}/lib/remote.sh"

WITH_SEARCH=0
SYNC_ONLY=0

usage() {
  sed -n '2,22p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) AURA_DRY_RUN=1; shift ;;
    --with-search) WITH_SEARCH=1; shift ;;
    --sync-only) SYNC_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

export AURA_DRY_RUN
aura_load_node1_env
aura_use_node_ssh_user 4
aura_require_host "${AURA_NODE4_HOST:-}" "AURA_NODE4_HOST"

echo "==> Node 4 deploy → ${AURA_SSH_USER}@${AURA_NODE4_HOST}:${AURA_REMOTE_APP_ROOT}"
aura_rsync "${AURA_NODE4_HOST}"

if [[ "${SYNC_ONLY}" == "1" ]]; then
  echo "==> Sync-only; skipping container recreate"
  exit 0
fi

# Ensure a remote .env exists (created once by ops; never overwritten by rsync).
if [[ "${AURA_DRY_RUN}" != "1" ]]; then
  if ! aura_ssh "${AURA_NODE4_HOST}" \
    "test -f '${AURA_REMOTE_APP_ROOT}/deploy/node4/.env'"; then
    echo "error: ${AURA_REMOTE_APP_ROOT}/deploy/node4/.env missing on Node 4" >&2
    echo "  On Node 4 (once):" >&2
    echo "    cd ${AURA_REMOTE_APP_ROOT}/deploy/node4" >&2
    echo "    cp .env.node4.example .env && \$EDITOR .env" >&2
    exit 1
  fi
fi

echo "==> Recreating prometheus + grafana (Qdrant untouched)"
aura_remote_compose "${AURA_NODE4_HOST}" node4 \
  up -d --no-deps --force-recreate --no-build prometheus grafana

if [[ "${WITH_SEARCH}" == "1" ]]; then
  echo "==> Rebuilding embedding-reranker (--with-search)"
  aura_remote_compose "${AURA_NODE4_HOST}" node4 \
    up -d --no-deps --build --force-recreate embedding-reranker
fi

if [[ "${AURA_DRY_RUN}" == "1" ]]; then
  echo "==> Dry-run complete"
  exit 0
fi

echo "==> Health check (Prometheus on Node 4 localhost:9090)"
aura_ssh "${AURA_NODE4_HOST}" \
  "curl -fsS --max-time 15 http://127.0.0.1:9090/-/healthy >/dev/null" \
  || {
    echo "warning: Prometheus health endpoint not reachable yet" >&2
    aura_remote_compose "${AURA_NODE4_HOST}" node4 ps
    exit 1
  }

echo "==> Node 4 deploy complete"
aura_remote_compose "${AURA_NODE4_HOST}" node4 ps prometheus grafana
