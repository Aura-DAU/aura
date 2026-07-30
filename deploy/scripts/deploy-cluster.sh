#!/usr/bin/env bash
# Orchestrate AURA cluster deploys from Node 1.
#
# By default runs Node 1 app deploy only (same as deploy-apps.sh).
# Opt in to remotes with flags — Node 2/3 never restart vLLM unless asked.
#
# Flags:
#   --apps              Deploy Node 1 aura+backend+nginx (default if no remote flags)
#   --node4             Sync + recreate prometheus/grafana on Node 4
#   --node4-search      Same as --node4 plus rebuild embedding-reranker
#   --node2             Sync Node 2 (no vLLM restart)
#   --node3             Sync Node 3 (no vLLM restart)
#   --node2-restart     Sync Node 2 and recreate vLLM
#   --node3-restart     Sync Node 3 and recreate vLLM
#   --all-safe          Node 1 apps + Node 4 monitoring + Node 2/3 sync (no vLLM restart)
#   --dry-run           Pass through to remote scripts
#   <ref>               Optional git ref for Node 1 apps (default: main)
#
# Usage:
#   ./deploy/scripts/deploy-cluster.sh --node4
#   ./deploy/scripts/deploy-cluster.sh --all-safe main
#   ./deploy/scripts/deploy-cluster.sh --node2-restart --node3-restart

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DO_APPS=0
DO_NODE2=0
DO_NODE3=0
DO_NODE4=0
NODE2_RESTART=0
NODE3_RESTART=0
NODE4_SEARCH=0
DRY_ARGS=()
REF="main"
EXPLICIT=0

usage() {
  sed -n '2,24p' "$0" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apps) DO_APPS=1; EXPLICIT=1; shift ;;
    --node4) DO_NODE4=1; EXPLICIT=1; shift ;;
    --node4-search) DO_NODE4=1; NODE4_SEARCH=1; EXPLICIT=1; shift ;;
    --node2) DO_NODE2=1; EXPLICIT=1; shift ;;
    --node3) DO_NODE3=1; EXPLICIT=1; shift ;;
    --node2-restart) DO_NODE2=1; NODE2_RESTART=1; EXPLICIT=1; shift ;;
    --node3-restart) DO_NODE3=1; NODE3_RESTART=1; EXPLICIT=1; shift ;;
    --all-safe)
      DO_APPS=1
      DO_NODE2=1
      DO_NODE3=1
      DO_NODE4=1
      EXPLICIT=1
      shift
      ;;
    --dry-run) DRY_ARGS+=(--dry-run); shift ;;
    -h|--help) usage; exit 0 ;;
    -*)
      echo "error: unknown flag: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      REF="$1"
      shift
      ;;
  esac
done

# No remote flags → Node 1 apps only (backward-compatible default).
if [[ "${EXPLICIT}" == "0" ]]; then
  DO_APPS=1
fi

chmod +x \
  "${SCRIPT_DIR}/deploy-apps.sh" \
  "${SCRIPT_DIR}/deploy-node2.sh" \
  "${SCRIPT_DIR}/deploy-node3.sh" \
  "${SCRIPT_DIR}/deploy-node4.sh"

if [[ "${DO_APPS}" == "1" ]]; then
  echo "==> [cluster] Node 1 applications"
  "${SCRIPT_DIR}/deploy-apps.sh" "${REF}"
fi

# Bash + set -u: expanding an empty array with "${arr[@]}" errors on some versions.
if [[ "${DO_NODE4}" == "1" ]]; then
  echo "==> [cluster] Node 4 monitoring"
  if [[ "${NODE4_SEARCH}" == "1" && ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node4.sh" "${DRY_ARGS[@]}" --with-search
  elif [[ "${NODE4_SEARCH}" == "1" ]]; then
    "${SCRIPT_DIR}/deploy-node4.sh" --with-search
  elif [[ ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node4.sh" "${DRY_ARGS[@]}"
  else
    "${SCRIPT_DIR}/deploy-node4.sh"
  fi
fi

if [[ "${DO_NODE2}" == "1" ]]; then
  echo "==> [cluster] Node 2"
  if [[ "${NODE2_RESTART}" == "1" && ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node2.sh" "${DRY_ARGS[@]}" --restart-vllm
  elif [[ "${NODE2_RESTART}" == "1" ]]; then
    "${SCRIPT_DIR}/deploy-node2.sh" --restart-vllm
  elif [[ ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node2.sh" "${DRY_ARGS[@]}"
  else
    "${SCRIPT_DIR}/deploy-node2.sh"
  fi
fi

if [[ "${DO_NODE3}" == "1" ]]; then
  echo "==> [cluster] Node 3"
  if [[ "${NODE3_RESTART}" == "1" && ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node3.sh" "${DRY_ARGS[@]}" --restart-vllm
  elif [[ "${NODE3_RESTART}" == "1" ]]; then
    "${SCRIPT_DIR}/deploy-node3.sh" --restart-vllm
  elif [[ ${#DRY_ARGS[@]} -gt 0 ]]; then
    "${SCRIPT_DIR}/deploy-node3.sh" "${DRY_ARGS[@]}"
  else
    "${SCRIPT_DIR}/deploy-node3.sh"
  fi
fi

echo "==> Cluster deploy finished"
