# Shared SSH/rsync helpers for AURA multi-node deploys from Node 1.
# Sourced by deploy-node{2,3,4}.sh and deploy-cluster.sh — not executed directly.
#
# Expected env (set by caller or deploy/node1/.env):
#   AURA_SSH_USER            default SSH user for remotes (default: aura)
#   AURA_NODE{2,3,4}_SSH_USER  per-node override (e.g. aura4)
#   AURA_SSH_KEY             default: /opt/aura/.ssh/cluster_deploy
#   AURA_REMOTE_APP_ROOT     default: /opt/aura/app
#   AURA_APP_ROOT            local checkout (default: /opt/aura/app)
#   AURA_DRY_RUN             if "1", print actions only

: "${AURA_SSH_USER:=aura}"
: "${AURA_SSH_KEY:=/opt/aura/.ssh/cluster_deploy}"
: "${AURA_REMOTE_APP_ROOT:=/opt/aura/app}"
: "${AURA_APP_ROOT:=/opt/aura/app}"
: "${AURA_DRY_RUN:=0}"

# Apply per-node SSH user override if set (AURA_NODE4_SSH_USER, etc.).
aura_use_node_ssh_user() {
  local node="$1"
  local override_var="AURA_NODE${node}_SSH_USER"
  local override="${!override_var:-}"
  if [[ -n "${override}" ]]; then
    AURA_SSH_USER="${override}"
    export AURA_SSH_USER
  fi
}

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
    echo "  Add it to ${AURA_APP_ROOT}/deploy/node1/.env (or /opt/aura/.env), e.g.:" >&2
    echo "    AURA_NODE4_HOST=10.x.x.x" >&2
    echo "  (no spaces around '=', do not leave the line commented with #)" >&2
    echo "  Or export it for this shell: export ${label}=10.x.x.x" >&2
    echo "  Checked: AURA_ENV_FILE=${AURA_ENV_FILE:-unset}," >&2
    echo "           ${AURA_APP_ROOT}/deploy/node1/.env," >&2
    echo "           /opt/aura/.env" >&2
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

  # Repo layout: deploy configs live under .github/deploy/. Remote nodes still
  # receive them at ${AURA_REMOTE_APP_ROOT}/deploy/ (install path unchanged).
  local local_deploy="${AURA_APP_ROOT}/.github/deploy"
  if [[ ! -d "${local_deploy}" ]]; then
    local_deploy="${AURA_APP_ROOT}/deploy"
  fi
  if [[ ! -d "${local_deploy}" ]]; then
    echo "error: local deploy missing under ${AURA_APP_ROOT}/.github/deploy (or deploy/)" >&2
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

  # Skip per-node secrets and Node-1-only TLS material (often root-only readable).
  # Example templates (.env.*.example) still sync.
  echo "==> Syncing ${local_deploy}/ → ${host}:${AURA_REMOTE_APP_ROOT}/deploy/"
  rsync "${rsync_flags[@]}" \
    -e "${ssh_e}" \
    --exclude '.env' \
    --exclude 'certs/' \
    --exclude 'node_modules/' \
    --exclude '.DS_Store' \
    "${local_deploy}/" \
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

# Load cluster host vars from Node 1 env file(s) if not already exported.
# Merges across candidates: earlier files win for a given key; later files
# fill keys that are still empty (so legacy /opt/aura/.env still works when
# deploy/node1/.env exists but lacks AURA_NODE*_HOST).
aura_load_node1_env() {
  local candidates=(
    "${AURA_ENV_FILE:-}"
    "${AURA_APP_ROOT}/.github/deploy/node1/.env"
    "${AURA_APP_ROOT}/deploy/node1/.env"
    "/opt/aura/.env"
  )
  local f key val line
  local found_any=0
  for f in "${candidates[@]}"; do
    [[ -z "${f}" || ! -f "${f}" ]] && continue
    found_any=1
    while IFS= read -r line || [[ -n "${line}" ]]; do
      # Trim leading whitespace; skip blanks and comments.
      line="${line#"${line%%[![:space:]]*}"}"
      [[ -z "${line}" || "${line}" == \#* ]] && continue
      # Optional "export " prefix; optional spaces around "=".
      if [[ "${line}" =~ ^(export[[:space:]]+)?(AURA_NODE[234]_HOST|AURA_NODE[234]_SSH_USER|AURA_SSH_USER|AURA_SSH_KEY|AURA_REMOTE_APP_ROOT)[[:space:]]*=[[:space:]]*(.*)$ ]]; then
        key="${BASH_REMATCH[2]}"
        val="${BASH_REMATCH[3]}"
        # Strip trailing inline comment (unquoted # ...) and surrounding quotes.
        if [[ "${val}" != \"*\" && "${val}" != \'*\' ]]; then
          val="${val%%\#*}"
          val="${val%"${val##*[![:space:]]}"}"
        fi
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
  done
  if [[ "${found_any}" -eq 0 ]]; then
    echo "warning: no Node 1 env file found (tried AURA_ENV_FILE, ${AURA_APP_ROOT}/deploy/node1/.env, /opt/aura/.env)" >&2
  fi
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
