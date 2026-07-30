#!/usr/bin/env bash
# Deploy Node 2 (vLLM) from Node 1 via SSH/rsync.
#
# Default (safe): sync deploy/ (+ services/) only. Does NOT restart vLLM.
# GPU cold-starts are expensive — pass --restart-vllm only when compose or
# model settings actually need a recreate.
#
# Flags:
#   --dry-run        Print actions; rsync --dry-run
#   --restart-vllm   Recreate the vllm-node1 service after sync
#   --sync-only      Alias for default (explicit)
#
# Required env:
#   AURA_NODE2_HOST
#
# Usage (on Node 1):
#   AURA_NODE2_HOST=10.x.x.2 ./deploy/scripts/deploy-node2.sh
#   ./deploy/scripts/deploy-node2.sh --restart-vllm

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/remote.sh
source "${SCRIPT_DIR}/lib/remote.sh"

RESTART_VLLM=0

usage() {
  sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) AURA_DRY_RUN=1; shift ;;
    --restart-vllm) RESTART_VLLM=1; shift ;;
    --sync-only) RESTART_VLLM=0; shift ;;
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
aura_use_node_ssh_user 2
aura_require_host "${AURA_NODE2_HOST:-}" "AURA_NODE2_HOST"

echo "==> Node 2 deploy → ${AURA_SSH_USER}@${AURA_NODE2_HOST}:${AURA_REMOTE_APP_ROOT}"
if ! aura_check_ssh "${AURA_NODE2_HOST}"; then
  echo "==> [WARNING] Node 2 (${AURA_SSH_USER}@${AURA_NODE2_HOST}) is not reachable via SSH."
  echo "==> Skipping Node 2 deploy step without breaking the build pipeline."
  exit 0
fi
aura_rsync "${AURA_NODE2_HOST}"

if [[ "${RESTART_VLLM}" != "1" ]]; then
  echo "==> Sync complete (vLLM not restarted; pass --restart-vllm to recreate)"
  exit 0
fi

if [[ "${AURA_DRY_RUN}" != "1" ]]; then
  if ! aura_ssh "${AURA_NODE2_HOST}" \
    "test -f '${AURA_REMOTE_APP_ROOT}/deploy/node2/.env'"; then
    echo "error: ${AURA_REMOTE_APP_ROOT}/deploy/node2/.env missing on Node 2" >&2
    echo "  On Node 2 (once): cp .env.node2.example .env && edit" >&2
    exit 1
  fi
fi

echo "==> Recreating vllm-node1 (--restart-vllm)"
aura_remote_compose "${AURA_NODE2_HOST}" node2 \
  up -d --no-deps --force-recreate --no-build vllm-node1

if [[ "${AURA_DRY_RUN}" == "1" ]]; then
  echo "==> Dry-run complete"
  exit 0
fi

echo "==> Node 2 deploy complete"
aura_remote_compose "${AURA_NODE2_HOST}" node2 ps
