# Runbook — Reading AURA metrics during an incident (EDGE-03)

Prometheus and Grafana on Node 4 bind to **loopback only**
(`.github/deploy/node4/docker-compose.yml`: `127.0.0.1:9090` and
`127.0.0.1:3000`). The public edge hard-denies the unauthenticated scrape
endpoint (`location /backend/metrics { deny all; return 404; }`). Both are
correct security defaults. This runbook is the sanctioned way for an
operator to reach the dashboards without widening network exposure.

Do **not** open Grafana or Prometheus to the LAN or the public internet
from this runbook. See the "Recommended alternative" section at the end —
that change needs an explicit human approval.

---

## Hosts and ports

| Role | Host (LAN) | Service | Loopback port |
|------|------------|---------|---------------|
| Gateway / FastAPI / nginx | `10.100.97.71` (Node 1) | backend `/metrics` | `8000` (private; scrape from Node 4) |
| vLLM (gateway GPU) | `10.100.97.71` | vLLM `/metrics` | published as **`8001`** |
| vLLM | `10.100.97.72` (Node 2) | vLLM `/metrics` | `8000` |
| vLLM | `10.100.97.73` (Node 3) | vLLM `/metrics` | `8000` |
| Prometheus + Grafana | `10.100.97.74` (Node 4) | Prometheus | `127.0.0.1:9090` |
| | | Grafana | `127.0.0.1:3000` |

SSH user / key: whatever is configured for cluster deploy
(`AURA_SSH_USER`, `AURA_SSH_KEY`, `AURA_NODE4_HOST` in
`.github/deploy/node1/.env.node1.example`). Substitute your login below.

---

## 1. Tunnel Grafana (and Prometheus) from Node 4

From your laptop:

```bash
# Replace USER and NODE4 with the deploy SSH principal / host.
ssh -N \
  -L 3000:127.0.0.1:3000 \
  -L 9090:127.0.0.1:9090 \
  USER@NODE4
```

Then open:

- Grafana: <http://127.0.0.1:3000> — login with `GRAFANA_ADMIN_PASSWORD`
- Prometheus: <http://127.0.0.1:9090> — raw queries / target health

Keep the SSH session open for the duration of the incident. Close it when
you are done; nothing is left exposed.

If you can only SSH to Node 1 (gateway jump host):

```bash
ssh -N \
  -J USER@NODE1 \
  -L 3000:127.0.0.1:3000 \
  -L 9090:127.0.0.1:9090 \
  USER@NODE4
```

---

## 2. What to look at first during a routing incident

Open the **AURA System Observability** dashboard
(`uid: aura-system-overview`).

1. **Inference Dispatch Share (5m)** and **vLLM Dispatched Requests per
   Node**. These are `aura_inference_node_requests_total` from the FastAPI
   gateway. After OBS-01 (multiprocess collection) is deployed they are
   trustworthy across every gunicorn worker. Under load every healthy node
   should take a non-zero share; a persistent 80–100% pin on one node is
   the GPU-01 / GPU-07 failure mode.
2. **vLLM Inference Engine Queue & Running Requests**
   (`vllm:num_requests_running` / `vllm:num_requests_waiting`). Cross-check
   the backend dispatch share against the real GPU queues — a node with
   `waiting=0` that is still receiving most of the traffic means the router
   is blind to queue depth (GPU-07).
3. **Backend Request Rate** and **Request Latency P95** — confirm the
   symptom is load / routing and not a total outage.
4. Prometheus → Status → Targets. `node1-gateway-backend`,
   `vllm-inference-nodes` (all three, including `10.100.97.71:8001`), and
   `node4-embedding-reranker` should be UP. A red vLLM target on the
   gateway node usually means the scrape is hitting FastAPI `:8000`
   instead of vLLM `:8001`.

### Quick PromQL (Prometheus UI)

```promql
# Absolute dispatches in the last 5 minutes — the number to quote in the incident log
sum by (node) (increase(aura_inference_node_requests_total[5m]))

# Share of the pool
sum by (node) (increase(aura_inference_node_requests_total[5m]))
  / scalar(sum(increase(aura_inference_node_requests_total[5m])))

# Live GPU queues (vLLM's own metrics — independent of OBS-01)
vllm:num_requests_running
vllm:num_requests_waiting
```

### Direct curl when Grafana is unreachable

From Node 1 (private network, not through the edge):

```bash
# Aggregated backend counters (requires PROMETHEUS_MULTIPROC_DIR on the
# backend container — see OBS-01). Ten rapid scrapes must agree.
for i in 1 2 3 4 5; do
  curl -fsS http://127.0.0.1:8000/metrics \
    | grep '^aura_inference_node_requests_total'
  sleep 0.2
done

# Per-node vLLM queues — ground truth when the backend counters are suspect
curl -fsS http://127.0.0.1:8001/metrics | grep -E 'num_requests_(running|waiting)'
curl -fsS http://10.100.97.72:8000/metrics | grep -E 'num_requests_(running|waiting)'
curl -fsS http://10.100.97.73:8000/metrics | grep -E 'num_requests_(running|waiting)'
```

Do **not** try `https://<public>/backend/metrics` — the edge returns 404 by
design.

---

## 3. Confirm OBS-01 is actually on before trusting the counters

On the backend container:

```bash
docker compose exec backend printenv PROMETHEUS_MULTIPROC_DIR
# expect: /var/lib/aura/prometheus   (or whatever was configured)

docker compose exec backend ls -la /var/lib/aura/prometheus
# expect: one counter_*.db (and histogram_*.db) per live worker

docker compose logs backend 2>&1 | grep '\[metrics\]' | tail
# expect: "multiprocess dir … ready" from the gunicorn master, and
#         "multiprocess mode enabled at …" from each worker
```

If `PROMETHEUS_MULTIPROC_DIR` is unset, `/metrics` still answers (it falls
back to a per-worker registry) but the values will alternate across scrapes
exactly as OBS-01 described. Trust the vLLM queue metrics instead until
the env var is wired through compose and the container is redeployed.

---

## Recommended alternative (needs human approval — do not apply from this runbook)

**Put Grafana behind the authenticated edge**, e.g. `https://aura.dau.ac.in/grafana/`
proxied to Node 4's loopback Grafana, gated by the same NextAuth / SSO
session the rest of the app uses (or at minimum HTTP basic auth + IP allowlist).

| | SSH tunnel (this runbook) | Grafana behind authenticated edge |
|--|--|--|
| Exposure | Zero — loopback only, operator-initiated | Public hostname, auth-gated |
| Incident access | Requires SSH to Node 4 (or a jump) | Browser, any operator with an account |
| Ops cost | Documented commands; rediscovered mid-incident today | One nginx `location` + auth wiring |
| Blast radius of a misconfig | None | Accidental unauthenticated Grafana = full metric + admin surface |
| Prometheus UI | Still tunnel-only (leave it that way) | Leave on loopback; only Grafana needs the edge |

**Recommendation to the operator / orchestrator:** keep Prometheus and the
raw `/metrics` endpoints private (current posture), and approve a follow-up
change that proxies **Grafana only** through the authenticated edge. Reject
any change that publishes `9090`/`3000` on `0.0.0.0` or that lifts the
`/backend/metrics` deny. Until that approval lands, this SSH-tunnel runbook
is the sanctioned path.
