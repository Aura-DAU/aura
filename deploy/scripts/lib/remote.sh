# Shared SSH/rsync helpers for AURA multi-node deploys from Node 1.
# Sourced by deploy-node{2,3,4}.sh and deploy-cluster.sh — not executed directly.
#
# Expected env (set by caller or deploy/node1/.env):
#   AURA_SSH_USER          default: aura
#   AURA_SSH_KEY           default: /opt/aura/.ssh/cluster_deploy
#   AURA_REMOTE_APP_ROOT   default: /opt/aura/app
#   AURA_APP_ROOT          local checkout (default: /opt/aura/app)
#   AURA_DRY_RUN           if "1", print actions only

: "${AURA_SSH_USER:=aura}"
: "${AURA_SSH_KEY:=/opt/aura/.ssh/cluster_deploy}"
: "${AURA_REMOTE_APP_ROOT:=/opt/aura/app}"
: "${AURA_APP_ROOT:=/opt/aura/app}"
: "${AURA_DRY_RUN:=0}"

aura_require_cmd() {
  local cmd
  for cmd in "$@"; do
    if ! command -v "${cmd}" >/dev/null 2>&1; then
      echo "error: required command not found: ${cmd}" >&2
      return 1
    fi
  done
}

aura_require_ssh_key() {
  if [[ ! -f "${AURA_SSH_KEY}" ]]; then
    echo "error: SSH key not found: ${AURA_SSH_KEY}" >&2
    echo "  On Node 1 (once):" >&2
    echo "    ssh-keygen -t ed25519 -f /opt/aura/.ssh/cluster_deploy -N \"\"" >&2
    echo "    ssh-copy-id -i /opt/aura/.ssh/cluster_deploy.pub ${AURA_SSH_USER}@<NODE_IP>" >&2
    return 1
  fi
}

aura_require_host() {
  local host="${1:-}"
  local label="${2:-remote host}"
  if [[ -z "${host}" ]]; then
    echo "error: ${label} is not set" >&2
    echo "  Export AURA_NODE{2,3,4}_HOST or add it to deploy/node1/.env" >&2
    return 1
  fi
}

# Print ssh -o/-i options as separate lines (safe for array consumption).
aura_ssh_opts_lines() {
  printf '%s\n' \
    -i "${AURA_SSH_KEY}" \
    -o IdentitiesOnly=yes \
    -o BatchMode=yes \
    -o StrictHostKeyChecking=accept-new \
    -o ConnectTimeout=15
}

aura_ssh() {
  local host="$1"
  shift
  local -a opts=()
  local opt
  while IFS= read -r opt; do
    [[ -n "${opt}" ]] && opts+=("${opt}")
  done < <(aura_ssh_opts_lines)

  aura_require_cmd ssh
  aura_require_ssh_key
  aura_require_host "${host}" "SSH host"
  if [[ "${AURA_DRY_RUN}" == "1" ]]; then
    echo "[dry-run] ssh ${AURA_SSH_USER}@${host} $*"
    return 0
  fi
  ssh "${opts[@]}" "${AURA_SSH_USER}@${host}" "$@"
}

# Sync deploy/ + services/ to the remote app root. Never overwrites remote .env files.
aura_rsync() {
  local host="$1"
  local -a opts=()
  local opt
  while IFS= read -r opt; do
    [[ -n "${opt}" ]] && opts+=("${opt}")
  done < <(aura_ssh_opts_lines)

  aura_require_cmd rsync ssh
  aura_require_ssh_key
  aura_require_host "${host}" "rsync host"

  if [[ ! -d "${AURA_APP_ROOT}/deploy" ]]; then
    echo "error: local deploy/ missing under ${AURA_APP_ROOT}" >&2
    return 1
  fi

  # rsync -e needs a single command string; quote each option.
  local ssh_e="ssh"
  for opt in "${opts[@]}"; do
    ssh_e+=" $(printf '%q' "${opt}")"
  done

  local -a rsync_flags=(-a --delete --human-readable --info=stats1)
  if [[ "${AURA_DRY_RUN}" == "1" ]]; then
    rsync_flags+=(--dry-run)
    echo "[dry-run] rsync deploy/ + services/ → ${AURA_SSH_USER}@${host}:${AURA_REMOTE_APP_ROOT}/"
  else
    ssh "${opts[@]}" "${AURA_SSH_USER}@${host}" \
      "mkdir -p '${AURA_REMOTE_APP_ROOT}/deploy' '${AURA_REMOTE_APP_ROOT}/services'"
  fi

  # Only skip files named exactly .env (per-node secrets). Example templates sync.
  echo "==> Syncing deploy/ → ${host}:${AURA_REMOTE_APP_ROOT}/deploy/"
  rsync "${rsync_flags[@]}" \
    -e "${ssh_e}" \
    --exclude '.env' \
    --exclude 'node_modules/' \
    --exclude '.DS_Store' \
    "${AURA_APP_ROOT}/deploy/" \
    "${AURA_SSH_USER}@${host}:${AURA_REMOTE_APP_ROOT}/deploy/"

  if [[ -d "${AURA_APP_ROOT}/services" ]]; then
    echo "==> Syncing services/ → ${host}:${AURA_REMOTE_APP_ROOT}/services/"
    rsync "${rsync_flags[@]}" \
      -e "${ssh_e}" \
      --exclude 'node_modules/' \
      --exclude '__pycache__/' \
      --exclude '.cache/' \
      --exclude '*.pyc' \
      "${AURA_APP_ROOT}/services/" \
      "${AURA_SSH_USER}@${host}:${AURA_REMOTE_APP_ROOT}/services/"
  fi
}

# Load cluster host vars from Node 1 env file if not already exported.
aura_load_node1_env() {
  local candidates=(
    "${AURA_ENV_FILE:-}"
    "${AURA_APP_ROOT}/deploy/node1/.env"
    "/opt/aura/.env"
  )
  local f key val
  for f in "${candidates[@]}"; do
    [[ -z "${f}" || ! -f "${f}" ]] && continue
    while IFS= read -r line || [[ -n "${line}" ]]; do
      [[ -z "${line}" || "${line}" =~ ^[[:space:]]*# ]] && continue
      if [[ "${line}" =~ ^(AURA_NODE[234]_HOST|AURA_SSH_USER|AURA_SSH_KEY|AURA_REMOTE_APP_ROOT)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        val="${BASH_REMATCH[2]}"
        # Strip optional surrounding quotes.
        val="${val%\"}"
        val="${val#\"}"
        val="${val%\'}"
        val="${val#\'}"
        # Do not override an already-exported non-empty value.
        if [[ -z "${!key:-}" ]]; then
          export "${key}=${val}"
        fi
      fi
    done < "${f}"
    return 0
  done
  return 0
}

# Run docker compose on the remote node inside deploy/<subdir>.
aura_remote_compose() {
  local host="$1"
  local compose_subdir="$2"
  shift 2
  local remote_compose="${AURA_REMOTE_APP_ROOT}/deploy/${compose_subdir}"
  local quoted=()
  local arg
  for arg in "$@"; do
    quoted+=("$(printf '%q' "${arg}")")
  done
  aura_ssh "${host}" \
    "cd $(printf '%q' "${remote_compose}") && docker compose --env-file .env ${quoted[*]}"
}
