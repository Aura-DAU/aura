#!/usr/bin/env bash
# One-time install helper for the Node 1 GitHub Actions self-hosted runner.
#
# Installs under /opt/aura/actions-runner and registers label `aura-node1`
# so `.github/workflows/cd-auto-deploy.yml` can target this host.
#
# You still need a registration token from:
#   GitHub repo → Settings → Actions → Runners → New self-hosted runner
#
# Usage:
#   export RUNNER_TOKEN=...          # short-lived registration token
#   export GITHUB_REPO_URL=https://github.com/ossdaiict/DAU-pwa
#   sudo -u "$SUDO_USER" ./deploy/scripts/install-actions-runner.sh
#
# After install, start as a service (recommended):
#   sudo ./svc.sh install
#   sudo ./svc.sh start

set -euo pipefail

RUNNER_DIR="${AURA_RUNNER_DIR:-/opt/aura/actions-runner}"
REPO_URL="${GITHUB_REPO_URL:-https://github.com/ossdaiict/DAU-pwa}"
RUNNER_VERSION="${AURA_RUNNER_VERSION:-2.321.0}"
LABELS="${AURA_RUNNER_LABELS:-aura-node1}"

if [[ -z "${RUNNER_TOKEN:-}" ]]; then
  echo "error: set RUNNER_TOKEN to a GitHub Actions runner registration token" >&2
  exit 1
fi

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

if [[ ! -f ./config.sh ]]; then
  echo "==> Downloading GitHub Actions runner ${RUNNER_VERSION}"
  curl -fsSL -o actions-runner-linux-x64.tar.gz \
    "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
  tar xzf actions-runner-linux-x64.tar.gz
  rm -f actions-runner-linux-x64.tar.gz
fi

if [[ ! -f .runner ]]; then
  echo "==> Configuring runner (labels: ${LABELS})"
  ./config.sh --unattended \
    --url "${REPO_URL}" \
    --token "${RUNNER_TOKEN}" \
    --name "aura-node1" \
    --labels "${LABELS}" \
    --work "_work" \
    --replace
else
  echo "==> Runner already configured (.runner present); skipping config"
fi

echo "==> Runner ready under ${RUNNER_DIR}"
echo "    Start with:  cd ${RUNNER_DIR} && ./run.sh"
echo "    Or as a service: sudo ./svc.sh install && sudo ./svc.sh start"
echo "    CD workflow targets: runs-on: [self-hosted, Linux, aura-node1]"
