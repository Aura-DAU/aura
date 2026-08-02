#!/usr/bin/env python3
"""Load / capacity / resilience harness for the AURA InferenceRouter + vLLM pool.

Drives server/rag/pipeline/inference_router.py the same way the API does — many
threads calling InferenceRouter.call_with_rotation — while scraping every node's
own /metrics, so each run answers three questions at once:

  how fast is the pool   TTFT, decode rate, aggregate output tokens/s
  where did work land    per-node share, queue depth, KV-cache pressure
  what happens at the edge of capacity   queueing, 429s, failover, breaker trips

Commands:
  nodes      inventory + health of every VLLM_ENDPOINTS entry (catches the
             VLLM_MODEL/served-model mismatch that surfaces as a generic
             "Sorry, I encountered an error" in the UI)
  sweep      concurrency sweep to find the knee, then translate it into
             CHAT_CONCURRENCY / nginx limit_conn numbers
  soak       sustained load at fixed concurrency; watches for drift
  balance    routing fairness: does least-loaded + queue-aware spread work
  failover   injects a dead endpoint and verifies the breaker parks it

Router knobs are read from the environment at import time, so this script
applies --read-timeout/--connect-timeout/etc. to os.environ BEFORE importing
the pipeline package. Point it at a pool with --endpoints or an --env-file.

Run with the repo venv:
  server/.venv/bin/python loadtest/loadtest_inference_router.py sweep --help
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import statistics
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
SERVER_DIR = REPO_ROOT / "server"
for path in (SERVER_DIR, SERVER_DIR / "rag"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:
    import httpx
except ImportError:  # pragma: no cover - environment guard
    sys.exit("httpx is required. Use server/.venv/bin/python, or: pip install httpx")


# ── vLLM metrics ─────────────────────────────────────────────────────────────

def _metric(name: str) -> re.Pattern[str]:
    # Anchored with re.M so "# HELP"/"# TYPE" lines are skipped and per-reason
    # breakdowns (…_by_reason) are not summed a second time — same reasoning as
    # the router's own parser.
    return re.compile(rf"^{re.escape(name)}(?:\{{[^}}]*\}})?\s+(\S+)\s*$", re.M)


RUNNING_RE = _metric("vllm:num_requests_running")
WAITING_RE = _metric("vllm:num_requests_waiting")
# vLLM renamed this gauge across versions; accept either.
KV_RES = (_metric("vllm:kv_cache_usage_perc"), _metric("vllm:gpu_cache_usage_perc"))
GEN_TOKENS_RE = _metric("vllm:generation_tokens_total")
PROMPT_TOKENS_RE = _metric("vllm:prompt_tokens_total")


def sum_metric(pattern: re.Pattern[str], payload: str) -> float | None:
    total, found = 0.0, False
    for raw in pattern.findall(payload):
        try:
            total += float(raw)
        except (TypeError, ValueError):
            continue
        found = True
    return total if found else None


def metrics_url(node: str) -> str:
    base = node.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/metrics"


@dataclass
class NodeSample:
    t: float
    running: float | None
    waiting: float | None
    kv: float | None
    gen_tokens: float | None


class MetricsSampler:
    """Background /metrics poller — the node-side truth to set against our
    client-side timings. Never on the request path; failures are silent."""

    def __init__(self, nodes: Sequence[str], interval: float, timeout: float = 2.0):
        self.nodes = list(nodes)
        self.interval = interval
        self.timeout = timeout
        self.samples: dict[str, list[NodeSample]] = {n: [] for n in self.nodes}
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        if not self.nodes or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._loop, name="metrics-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.timeout + 2)
            self._thread = None

    def _loop(self) -> None:
        client = httpx.Client(timeout=httpx.Timeout(self.timeout))
        t0 = time.perf_counter()
        try:
            while not self._stop.is_set():
                for node in self.nodes:
                    try:
                        resp = client.get(metrics_url(node))
                        if resp.status_code != 200:
                            continue
                        body = resp.text
                    except Exception:  # noqa: BLE001 - sampling is best-effort
                        continue
                    kv = next((v for v in (sum_metric(p, body) for p in KV_RES)
                               if v is not None), None)
                    sample = NodeSample(
                        t=time.perf_counter() - t0,
                        running=sum_metric(RUNNING_RE, body),
                        waiting=sum_metric(WAITING_RE, body),
                        kv=kv,
                        gen_tokens=sum_metric(GEN_TOKENS_RE, body),
                    )
                    with self._lock:
                        self.samples[node].append(sample)
                self._stop.wait(self.interval)
        finally:
            client.close()

    def summary(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        with self._lock:
            for node, rows in self.samples.items():
                if not rows:
                    out[node] = {"samples": 0}
                    continue
                running = [r.running for r in rows if r.running is not None]
                waiting = [r.waiting for r in rows if r.waiting is not None]
                kv = [r.kv for r in rows if r.kv is not None]
                gen = [r.gen_tokens for r in rows if r.gen_tokens is not None]
                span = max(1e-6, rows[-1].t - rows[0].t)
                out[node] = {
                    "samples": len(rows),
                    "running_peak": max(running) if running else None,
                    "running_mean": statistics.fmean(running) if running else None,
                    "waiting_peak": max(waiting) if waiting else None,
                    "waiting_mean": statistics.fmean(waiting) if waiting else None,
                    "kv_peak": max(kv) if kv else None,
                    "kv_mean": statistics.fmean(kv) if kv else None,
                    "generated_tokens": (gen[-1] - gen[0]) if len(gen) >= 2 else None,
                    "node_tokens_per_s": ((gen[-1] - gen[0]) / span) if len(gen) >= 2 else None,
                }
        return out

    def reset(self) -> None:
        with self._lock:
            self.samples = {n: [] for n in self.nodes}


# ── Workload ─────────────────────────────────────────────────────────────────

FILLER = (
    "The university academic handbook states that a student must maintain the "
    "minimum attendance prescribed by the senate in every registered course, and "
    "that condonation is granted only on documented medical grounds approved by "
    "the dean of students. Course policy documents further specify the weightage "
    "of quizzes, mid semester examinations, laboratory work and the end semester "
    "examination, along with the grading scheme and the procedure for re-evaluation. "
)

QUESTIONS = [
    "Summarise the attendance and condonation policy in three sentences.",
    "What is the re-evaluation procedure and who approves it?",
    "How is the final grade computed from the components described above?",
    "List the documents a student must submit for medical condonation.",
    "Explain the difference between a mid semester and end semester weightage.",
]


@dataclass
class Workload:
    model: str
    prompt_tokens: int
    max_tokens: int
    stream: bool
    temperature: float
    shared_prefix: bool
    thinking: bool

    def build(self, rng: random.Random) -> list[dict[str, str]]:
        # ~4 chars per token is close enough for sizing a RAG-shaped prompt.
        target_chars = max(0, self.prompt_tokens * 4)
        context = (FILLER * (target_chars // len(FILLER) + 1))[:target_chars]
        # A unique marker defeats vLLM prefix caching, which would otherwise let
        # every request after the first skip prefill and report capacity the
        # production mix never sees. --shared-prefix measures the cached case.
        marker = "" if self.shared_prefix else f"[request {uuid.uuid4().hex}] "
        return [
            {"role": "system", "content": "You are AURA, the university assistant. Answer from the context."},
            {"role": "user", "content": f"{marker}Context:\n{context}\n\nQuestion: {rng.choice(QUESTIONS)}"},
        ]


@dataclass
class Result:
    t: float
    node: str
    attempts: list[str]
    ok: bool
    ttft: float | None
    total: float
    out_tokens: int
    err_type: str = ""
    err: str = ""

    @property
    def decode_rate(self) -> float | None:
        if not self.ok or self.ttft is None or self.out_tokens <= 1:
            return None
        decode = self.total - self.ttft
        return (self.out_tokens / decode) if decode > 0 else None


class Driver:
    """Issues requests either through the router (default) or straight at one
    endpoint, recording which node served each attempt.

    The node is read off the OpenAI client the router hands to `fn`, so a
    failover shows up as a second entry in `attempts` — no monkeypatching of
    router internals required.
    """

    def __init__(self, router: Any, workload: Workload, args: argparse.Namespace,
                 direct_client: Any | None = None, direct_node: str = ""):
        self.router = router
        self.workload = workload
        self.args = args
        self.direct_client = direct_client
        self.direct_node = direct_node
        self._usage_supported = True

    def _create(self, client: Any, messages: list[dict[str, str]]) -> Any:
        extra: dict[str, Any] = {}
        if not self.workload.thinking:
            # The router's own helper — a <think> preamble on a 32B model is
            # pure latency and would make every number here fiction.
            extra = self.router.no_think_extra_body()
        kwargs: dict[str, Any] = dict(
            model=self.workload.model,
            messages=messages,
            max_tokens=self.workload.max_tokens,
            temperature=self.workload.temperature,
            stream=self.workload.stream,
        )
        if extra:
            kwargs["extra_body"] = extra
        if self.workload.stream and self._usage_supported:
            kwargs["stream_options"] = {"include_usage": True}
        return client.chat.completions.create(**kwargs)

    def run_once(self, rng: random.Random, t0: float) -> Result:
        messages = self.workload.build(rng)
        attempts: list[str] = []
        started = time.perf_counter()

        def fn(client: Any) -> Any:
            attempts.append(str(client.base_url).rstrip("/"))
            return self._create(client, messages)

        try:
            if self.direct_client is not None:
                attempts.append(self.direct_node)
                result = self._create(self.direct_client, messages)
            else:
                result = self.router.call_with_rotation(
                    fn, max_retries=self.args.max_retries,
                    initial_retry_delay=self.args.retry_delay,
                )
            ttft, tokens = self._consume(result, started)
        except Exception as exc:  # noqa: BLE001 - every failure mode is data here
            msg = str(exc)
            if self.workload.stream and "stream_options" in msg:
                self._usage_supported = False  # older vLLM; fall back to counting deltas
            return Result(started - t0, attempts[-1] if attempts else "-", attempts,
                          False, None, time.perf_counter() - started, 0,
                          type(exc).__name__, msg[:200])
        return Result(started - t0, attempts[-1] if attempts else "-", attempts,
                      True, ttft, time.perf_counter() - started, tokens)

    def _consume(self, result: Any, started: float) -> tuple[float | None, int]:
        if not self.workload.stream:
            usage = getattr(result, "usage", None)
            tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            return None, tokens
        ttft: float | None = None
        tokens = 0
        usage_tokens = 0
        try:
            for chunk in result:
                usage = getattr(chunk, "usage", None)
                if usage is not None and getattr(usage, "completion_tokens", None):
                    usage_tokens = int(usage.completion_tokens)
                choices = getattr(chunk, "choices", None) or []
                if not choices:
                    continue
                delta = getattr(choices[0], "delta", None)
                content = getattr(delta, "content", None) if delta else None
                if content:
                    if ttft is None:
                        ttft = time.perf_counter() - started
                    tokens += 1
        finally:
            close = getattr(result, "close", None)
            if callable(close):
                close()
        return ttft, usage_tokens or tokens


# ── Run orchestration ────────────────────────────────────────────────────────

@dataclass
class RunOutcome:
    results: list[Result]
    wall: float
    metrics: dict[str, Any]


def ensure_fd_headroom(needed: int) -> str:
    """Raise RLIMIT_NOFILE toward the hard limit before a high-concurrency run.

    Each in-flight generation holds its own socket to a node; macOS ships a
    soft limit of 256, so a 1000-way run dies with "Too many open files" and
    the failure looks like the pool's fault.
    """
    try:
        import resource  # noqa: PLC0415 - POSIX only
    except ImportError:  # pragma: no cover - Windows
        return "fd limit: not adjustable on this platform"
    want = needed + 256
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    if soft >= want:
        return f"fd limit: {soft} (need ~{want})"
    target = want if hard == resource.RLIM_INFINITY else min(hard, want)
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (target, hard))
        soft = target
    except (ValueError, OSError) as exc:
        return (f"fd limit: {soft}, could not raise to {want} ({exc}). "
                f"Run `ulimit -n {want}` first or lower the concurrency.")
    return f"fd limit: raised to {soft}"


def check_scale(concurrency: int, router: Any) -> None:
    """Print the harness-side ceilings that would otherwise be misread as
    pool limits: file descriptors and the router's own httpx pool."""
    print(ensure_fd_headroom(concurrency))
    max_conns = getattr(router, "_MAX_CONNECTIONS", 0)
    if concurrency > max_conns:
        print(f"NOTE: concurrency {concurrency} exceeds VLLM_MAX_CONNECTIONS={max_conns}; "
              f"requests will queue in the client pool and inflate TTFT. "
              f"Raise it with --max-connections {concurrency + 64}.")
    if concurrency > 512:
        print(f"NOTE: {concurrency} worker threads — expect harness CPU overhead; "
              f"consider splitting the run across machines.")


def run_workload(driver: Driver, concurrency: int, *, requests: int | None = None,
                 duration: float | None = None, sampler: MetricsSampler | None = None,
                 seed: int = 7, progress_every: float = 0.0,
                 label: str = "") -> RunOutcome:
    results: list[Result] = []
    lock = threading.Lock()
    counter = {"issued": 0}
    stop_at = time.perf_counter() + duration if duration else None
    t0 = time.perf_counter()
    stop_flag = threading.Event()

    def worker(idx: int) -> None:
        rng = random.Random(seed * 1000 + idx)
        while not stop_flag.is_set():
            if stop_at is not None and time.perf_counter() >= stop_at:
                return
            with lock:
                if requests is not None and counter["issued"] >= requests:
                    return
                counter["issued"] += 1
            res = driver.run_once(rng, t0)
            with lock:
                results.append(res)

    reporter: threading.Thread | None = None
    if progress_every > 0:
        def report() -> None:
            last = 0
            while not stop_flag.wait(progress_every):
                with lock:
                    done, issued = len(results), counter["issued"]
                    recent = results[-min(len(results), 50):]
                rate = (done - last) / progress_every
                last = done
                ttfts = [r.ttft for r in recent if r.ttft is not None]
                print(f"    [{time.perf_counter() - t0:6.1f}s] {label} done={done:5d} "
                      f"inflight={issued - done:4d} rps={rate:6.2f} "
                      f"ttft_p50={_ms(pct(ttfts, 50))}ms", flush=True)
        reporter = threading.Thread(target=report, name="progress", daemon=True)
        reporter.start()

    if sampler is not None:
        sampler.reset()
        sampler.start()
    try:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(worker, i) for i in range(concurrency)]
            for f in futures:
                f.result()
    except KeyboardInterrupt:
        stop_flag.set()
        raise
    finally:
        stop_flag.set()
        if reporter is not None:
            reporter.join(timeout=progress_every + 1)
    wall = time.perf_counter() - t0
    metrics = sampler.summary() if sampler is not None else {}
    if sampler is not None:
        sampler.stop()
    return RunOutcome(results, wall, metrics)


# ── Stats ────────────────────────────────────────────────────────────────────

def pct(values: Sequence[float], p: float) -> float:
    vals = [v for v in values if v is not None]
    if not vals:
        return float("nan")
    ordered = sorted(vals)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * (p / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def _ms(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    return f"{v * 1000:.0f}"


def _f(v: float | None, fmt: str = "{:.2f}") -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    return fmt.format(v)


def summarise(outcome: RunOutcome) -> dict[str, Any]:
    results = outcome.results
    ok = [r for r in results if r.ok]
    ttfts = [r.ttft for r in ok if r.ttft is not None]
    lat = [r.total for r in ok]
    decode = [r.decode_rate for r in ok if r.decode_rate is not None]
    tokens = sum(r.out_tokens for r in ok)
    errs: dict[str, int] = {}
    for r in results:
        if not r.ok:
            errs[r.err_type] = errs.get(r.err_type, 0) + 1
    per_node: dict[str, dict[str, Any]] = {}
    for r in results:
        entry = per_node.setdefault(r.node, {"requests": 0, "ok": 0, "ttft": [], "total": []})
        entry["requests"] += 1
        if r.ok:
            entry["ok"] += 1
            if r.ttft is not None:
                entry["ttft"].append(r.ttft)
            entry["total"].append(r.total)
    nodes_out = {
        node: {
            "requests": e["requests"],
            "ok": e["ok"],
            "share": e["requests"] / max(1, len(results)),
            "ttft_p95_ms": pct(e["ttft"], 95) * 1000 if e["ttft"] else None,
            "e2e_p95_ms": pct(e["total"], 95) * 1000 if e["total"] else None,
        }
        for node, e in sorted(per_node.items())
    }
    retries = sum(max(0, len(r.attempts) - 1) for r in results)
    return {
        "requests": len(results),
        "ok": len(ok),
        "error_rate": 1 - (len(ok) / len(results)) if results else 0.0,
        "wall_s": outcome.wall,
        "req_per_s": len(ok) / max(1e-6, outcome.wall),
        "output_tokens": tokens,
        "output_tokens_per_s": tokens / max(1e-6, outcome.wall),
        "ttft_ms": {f"p{p}": pct(ttfts, p) * 1000 for p in (50, 90, 95, 99)} if ttfts else {},
        "e2e_ms": {f"p{p}": pct(lat, p) * 1000 for p in (50, 90, 95, 99)} if lat else {},
        "decode_tok_per_s_p50": pct(decode, 50) if decode else None,
        "failovers": retries,
        "errors": errs,
        "nodes": nodes_out,
        "node_metrics": outcome.metrics,
    }


def print_node_metrics(metrics: dict[str, Any], indent: str = "  ") -> None:
    live = {k: v for k, v in metrics.items() if v.get("samples")}
    if not live:
        print(f"{indent}(no /metrics samples — is VLLM_ENDPOINTS reachable from here?)")
        return
    print(f"{indent}{'node':<42}{'run pk':>8}{'wait pk':>9}{'KV pk':>8}{'KV avg':>8}{'node tok/s':>12}")
    for node, m in live.items():
        print(f"{indent}{_short(node):<42}{_f(m['running_peak'], '{:.0f}'):>8}"
              f"{_f(m['waiting_peak'], '{:.0f}'):>9}"
              f"{_f((m['kv_peak'] or 0) * 100, '{:.0f}%'):>8}"
              f"{_f((m['kv_mean'] or 0) * 100, '{:.0f}%'):>8}"
              f"{_f(m['node_tokens_per_s'], '{:.0f}'):>12}")


def _short(node: str) -> str:
    return node.replace("http://", "").replace("https://", "")


# ── Environment / router bootstrap ───────────────────────────────────────────

ENV_OVERRIDES = (
    ("connect_timeout", "VLLM_CONNECT_TIMEOUT"),
    ("read_timeout", "VLLM_READ_TIMEOUT"),
    ("breaker_threshold", "VLLM_BREAKER_THRESHOLD"),
    ("breaker_cooldown", "VLLM_BREAKER_COOLDOWN"),
    ("max_connections", "VLLM_MAX_CONNECTIONS"),
    ("max_keepalive", "VLLM_MAX_KEEPALIVE"),
)


def load_env_file(path: str) -> int:
    """Minimal KEY=VALUE loader. Existing environment wins, so an explicit
    export still overrides the file."""
    loaded = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
                loaded += 1
    return loaded


def bootstrap(args: argparse.Namespace) -> tuple[Any, list[str]]:
    """Apply env overrides, then import the router. Order matters: the router
    captures its timeout/breaker knobs as class attributes at import time, so
    anything set afterwards is silently ignored."""
    if args.env_file:
        n = load_env_file(args.env_file)
        print(f"loaded {n} variable(s) from {args.env_file}")
    if args.endpoints:
        os.environ["VLLM_ENDPOINTS"] = args.endpoints
    for attr, env_name in ENV_OVERRIDES:
        value = getattr(args, attr, None)
        if value is not None:
            os.environ[env_name] = str(value)
    if args.queue_aware is not None:
        os.environ["VLLM_QUEUE_AWARE"] = "1" if args.queue_aware else "0"

    from pipeline.inference_router import InferenceRouter  # noqa: PLC0415 - after env setup

    InferenceRouter._reset_for_tests()  # re-read VLLM_ENDPOINTS if already warm
    InferenceRouter._initialize()
    nodes = list(InferenceRouter._nodes)
    if not nodes:
        sys.exit("No vLLM endpoints configured. Pass --endpoints or --env-file.")
    return InferenceRouter, nodes


def make_workload(args: argparse.Namespace, router: Any) -> Workload:
    return Workload(
        model=args.model or router.model_name(),
        prompt_tokens=args.prompt_tokens,
        max_tokens=args.max_tokens,
        stream=not args.no_stream,
        temperature=args.temperature,
        shared_prefix=args.shared_prefix,
        thinking=args.thinking,
    )


def make_driver(args: argparse.Namespace, router: Any, workload: Workload) -> Driver:
    if args.via == "router":
        return Driver(router, workload, args)
    node = args.endpoint or router._nodes[0]
    client = router._client_for(node)  # same pooling/timeouts as production
    return Driver(router, workload, args, direct_client=client, direct_node=node)


def write_json(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    if not args.json:
        return
    with open(args.json, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    print(f"\nJSON report → {args.json}")


# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_nodes(args: argparse.Namespace) -> int:
    router, nodes = bootstrap(args)
    want_model = args.model or router.model_name()
    print(f"pool: {len(nodes)} node(s), expecting model {want_model!r}\n")
    report: dict[str, Any] = {"model": want_model, "nodes": {}}
    bad = 0
    with httpx.Client(timeout=httpx.Timeout(args.probe_timeout)) as client:
        for node in nodes:
            entry: dict[str, Any] = {}
            try:
                r = client.get(f"{node.rstrip('/')}/models",
                               headers={"Authorization": f"Bearer {os.getenv('VLLM_API_KEY', 'EMPTY')}"})
                served = [m.get("id") for m in r.json().get("data", [])] if r.status_code == 200 else []
                entry["status"] = r.status_code
                entry["served_models"] = served
            except Exception as exc:  # noqa: BLE001
                entry["error"] = f"{type(exc).__name__}: {exc}"
                served = []
            try:
                m = client.get(metrics_url(node))
                body = m.text if m.status_code == 200 else ""
            except Exception:  # noqa: BLE001
                body = ""
            entry["running"] = sum_metric(RUNNING_RE, body) if body else None
            entry["waiting"] = sum_metric(WAITING_RE, body) if body else None
            entry["kv"] = next((v for v in (sum_metric(p, body) for p in KV_RES)
                                if v is not None), None) if body else None
            entry["metrics_reachable"] = bool(body)

            problems = []
            if entry.get("error") or entry.get("status") != 200:
                problems.append("unreachable /v1/models")
            elif want_model not in (served or []):
                # This exact mismatch is what turns into a 404 from vLLM and a
                # generic error bubble in the frontend.
                problems.append(f"model mismatch: serves {served}")
            if not body:
                problems.append("no /metrics (queue-aware routing degrades to local counts)")
            entry["problems"] = problems
            bad += bool(problems)
            report["nodes"][node] = entry

            flag = "ok " if not problems else "!! "
            print(f"  {flag}{_short(node):<40} status={entry.get('status', '-')} "
                  f"running={_f(entry['running'], '{:.0f}')} waiting={_f(entry['waiting'], '{:.0f}')} "
                  f"kv={_f((entry['kv'] or 0) * 100, '{:.0f}%')}")
            for p in problems:
                print(f"       ↳ {p}")
    write_json(args, report)
    return 1 if (bad and args.strict) else 0


def cmd_sweep(args: argparse.Namespace) -> int:
    router, nodes = bootstrap(args)
    workload = make_workload(args, router)
    driver = make_driver(args, router, workload)
    sampler = MetricsSampler(nodes, args.sample_interval)
    levels = [int(x) for x in args.levels.split(",") if x.strip()]

    print(f"sweep via {args.via}: {len(nodes)} node(s), model {workload.model}, "
          f"prompt≈{workload.prompt_tokens} tok, max_tokens={workload.max_tokens}, "
          f"stream={workload.stream}, prefix_cache={'shared' if workload.shared_prefix else 'defeated'}")
    check_scale(max(levels), router)
    print()

    if args.warmup:
        print(f"warmup: {args.warmup} request(s)…")
        run_workload(driver, min(args.warmup, 4), requests=args.warmup, seed=args.seed)

    rows: list[dict[str, Any]] = []
    for level in levels:
        n = args.requests_per_level or max(2 * level, 12)
        print(f"\n── concurrency {level} ({n} requests) ─────────────────────────")
        outcome = run_workload(driver, level, requests=n, sampler=sampler, seed=args.seed,
                               progress_every=args.progress_interval, label=f"c={level}")
        s = summarise(outcome)
        s["concurrency"] = level
        rows.append(s)
        print(f"    ok {s['ok']}/{s['requests']}  {s['req_per_s']:.2f} req/s  "
              f"{s['output_tokens_per_s']:.0f} out tok/s  "
              f"ttft p50/p95 {_ms(s['ttft_ms'].get('p50', float('nan')) / 1000)}/"
              f"{_ms(s['ttft_ms'].get('p95', float('nan')) / 1000)}ms  "
              f"e2e p95 {_ms(s['e2e_ms'].get('p95', float('nan')) / 1000)}ms  "
              f"failovers {s['failovers']}")
        print_node_metrics(s["node_metrics"], indent="    ")
        if s["errors"]:
            print(f"    errors: {s['errors']}")
        if level != levels[-1] and args.settle > 0:
            time.sleep(args.settle)

    print("\n" + "=" * 96)
    print("CONCURRENCY SWEEP")
    print("=" * 96)
    print(f"{'conc':>5}{'ok':>6}{'err%':>7}{'req/s':>8}{'out tok/s':>11}"
          f"{'ttft p50':>10}{'ttft p95':>10}{'e2e p95':>10}{'decode/req':>12}{'wait pk':>9}{'KV pk':>7}")
    for s in rows:
        peaks = [m for m in s["node_metrics"].values() if m.get("samples")]
        wait_pk = max((m["waiting_peak"] or 0) for m in peaks) if peaks else None
        kv_pk = max((m["kv_peak"] or 0) for m in peaks) if peaks else None
        print(f"{s['concurrency']:>5}{s['ok']:>6}{100 * s['error_rate']:>6.1f}%"
              f"{s['req_per_s']:>8.2f}{s['output_tokens_per_s']:>11.0f}"
              f"{_f(s['ttft_ms'].get('p50'), '{:.0f}'):>10}{_f(s['ttft_ms'].get('p95'), '{:.0f}'):>10}"
              f"{_f(s['e2e_ms'].get('p95'), '{:.0f}'):>10}"
              f"{_f(s['decode_tok_per_s_p50'], '{:.1f}'):>12}"
              f"{_f(wait_pk, '{:.0f}'):>9}{_f((kv_pk or 0) * 100, '{:.0f}%'):>7}")

    viable = [s for s in rows
              if s["error_rate"] <= args.max_error_rate
              and (not s["ttft_ms"] or s["ttft_ms"].get("p95", 0) <= args.ttft_slo_ms)]
    knee = max(viable, key=lambda s: s["output_tokens_per_s"]) if viable else None
    print("\nKnee analysis")
    if knee is None:
        print(f"  no level met the SLO (ttft p95 ≤ {args.ttft_slo_ms:.0f}ms, "
              f"err ≤ {100 * args.max_error_rate:.1f}%) — lower the load or check the pool")
    else:
        admitted = knee["concurrency"]
        print(f"  best sustainable concurrency: {admitted} "
              f"({knee['output_tokens_per_s']:.0f} out tok/s, "
              f"ttft p95 {_f(knee['ttft_ms'].get('p95'), '{:.0f}')}ms)")
        print(f"  per node (÷{len(nodes)}): ~{admitted / len(nodes):.1f} concurrent requests")
        per_process = admitted / max(1, args.api_replicas * args.backend_workers)
        print(f"  CHAT_CONCURRENCY ≈ {max(1, round(per_process))} "
              f"(for {args.api_replicas} replica(s) × {args.backend_workers} worker(s))")
        print(f"  nginx limit_conn aura_chat_total ≈ {2 * admitted} "
              f"(~one queue depth above admission, per .github/deploy/nginx.conf)")
        print("  Re-check nginx.conf's /api/chat limits whenever CHAT_CONCURRENCY changes.")

    write_json(args, {"levels": rows, "knee": knee, "nodes": nodes,
                      "workload": workload.__dict__})
    return 0 if knee is not None else 1


def cmd_soak(args: argparse.Namespace) -> int:
    router, nodes = bootstrap(args)
    workload = make_workload(args, router)
    driver = make_driver(args, router, workload)
    sampler = MetricsSampler(nodes, args.sample_interval)
    if args.duration is None and args.requests is None:
        args.duration = 300.0
    stop = " / ".join(filter(None, [
        f"{args.duration:.0f}s" if args.duration else "",
        f"{args.requests:,} requests" if args.requests else "",
    ]))
    print(f"soak: concurrency {args.concurrency} for {stop} "
          f"via {args.via}, model {workload.model}")
    check_scale(args.concurrency, router)
    print()
    outcome = run_workload(driver, args.concurrency, requests=args.requests,
                           duration=args.duration, sampler=sampler,
                           seed=args.seed, progress_every=args.progress_interval, label="soak")
    s = summarise(outcome)

    print("\n" + "=" * 78)
    print("SOAK")
    print("=" * 78)
    print(f"requests {s['requests']}  ok {s['ok']}  errors {100 * s['error_rate']:.2f}%  "
          f"{s['req_per_s']:.2f} req/s  {s['output_tokens_per_s']:.0f} out tok/s  "
          f"failovers {s['failovers']}")
    print(f"ttft ms  " + "  ".join(f"{k}={v:.0f}" for k, v in s["ttft_ms"].items()))
    print(f"e2e  ms  " + "  ".join(f"{k}={v:.0f}" for k, v in s["e2e_ms"].items()))
    if s["errors"]:
        print(f"errors   {s['errors']}")

    bucket = max(5.0, outcome.wall / 20)
    print(f"\nDrift ({bucket:.0f}s buckets)")
    print(f"  {'t(s)':>6}{'ok':>6}{'err':>6}{'req/s':>8}{'ttft p95':>10}{'e2e p95':>10}")
    buckets: dict[int, list[Result]] = {}
    for r in outcome.results:
        buckets.setdefault(int(r.t // bucket), []).append(r)
    for idx in sorted(buckets):
        rows = buckets[idx]
        ok = [r for r in rows if r.ok]
        print(f"  {idx * bucket:>6.0f}{len(ok):>6}{len(rows) - len(ok):>6}"
              f"{len(rows) / bucket:>8.2f}"
              f"{_ms(pct([r.ttft for r in ok if r.ttft is not None], 95)):>10}"
              f"{_ms(pct([r.total for r in ok], 95)):>10}")

    print("\nPer-node share")
    print(f"  {'node':<42}{'requests':>10}{'share':>8}{'ttft p95':>10}{'e2e p95':>10}")
    for node, e in s["nodes"].items():
        print(f"  {_short(node):<42}{e['requests']:>10}{100 * e['share']:>7.1f}%"
              f"{_f(e['ttft_p95_ms'], '{:.0f}'):>10}{_f(e['e2e_p95_ms'], '{:.0f}'):>10}")
    print("\nNode-side metrics")
    print_node_metrics(s["node_metrics"])
    print(f"\nRouter view: {json.dumps(router.stats(), default=str)}")

    write_json(args, {"soak": s, "router_stats": router.stats()})
    failed = s["error_rate"] > args.max_error_rate
    return 1 if failed else 0


def cmd_balance(args: argparse.Namespace) -> int:
    router, nodes = bootstrap(args)
    if args.via != "router":
        sys.exit("balance only makes sense --via router")
    if len(nodes) < 2:
        print("WARNING: only one node configured — balance has nothing to compare.\n")
    workload = make_workload(args, router)
    driver = Driver(router, workload, args)
    sampler = MetricsSampler(nodes, args.sample_interval)

    # A uniform workload hides bad routing: every node stays symmetric no matter
    # how requests are assigned. Mixing long and short generations is what makes
    # a least-loaded router visibly better (or worse) than round-robin.
    long_workload = Workload(**{**workload.__dict__, "max_tokens": workload.max_tokens * args.long_factor})
    long_driver = Driver(router, long_workload, args)

    print(f"balance: {args.requests} requests at concurrency {args.concurrency}, "
          f"{100 * args.long_ratio:.0f}% long ({long_workload.max_tokens} tok) / "
          f"{100 * (1 - args.long_ratio):.0f}% short ({workload.max_tokens} tok)")
    check_scale(args.concurrency, router)
    print()

    rng = random.Random(args.seed)
    mixed = MixedDriver(driver, long_driver, args.long_ratio, rng)
    outcome = run_workload(mixed, args.concurrency, requests=args.requests, sampler=sampler,
                           seed=args.seed, progress_every=args.progress_interval, label="balance")
    s = summarise(outcome)

    print("\n" + "=" * 78)
    print("ROUTING BALANCE")
    print("=" * 78)
    shares = {n: e["share"] for n, e in s["nodes"].items()}
    ideal = 1 / max(1, len(nodes))
    print(f"  {'node':<42}{'requests':>10}{'share':>8}{'vs ideal':>10}{'ttft p95':>10}")
    for node, e in s["nodes"].items():
        print(f"  {_short(node):<42}{e['requests']:>10}{100 * e['share']:>7.1f}%"
              f"{100 * (e['share'] - ideal):>9.1f}%{_f(e['ttft_p95_ms'], '{:.0f}'):>10}")
    skew = max(abs(v - ideal) for v in shares.values()) if shares else 0.0
    print(f"\n  max deviation from even split: {100 * skew:.1f} pp "
          f"(tolerance {100 * args.skew_tolerance:.1f} pp)")
    unused = [n for n in nodes if n not in shares]
    if unused:
        print(f"  NEVER SELECTED: {[_short(n) for n in unused]}")

    stats = router.stats()
    fresh = [n for n, v in stats.items() if v.get("queue_depth") is not None]
    print(f"  queue-aware samples live for {len(fresh)}/{len(nodes)} node(s)"
          + ("" if fresh else " — routing fell back to local in-flight counts only"))
    print("\nNode-side metrics")
    print_node_metrics(s["node_metrics"])

    write_json(args, {"balance": s, "skew": skew, "router_stats": stats})
    failed = skew > args.skew_tolerance or bool(unused) or s["error_rate"] > args.max_error_rate
    return 1 if failed else 0


class MixedDriver:
    """Alternates two drivers by ratio — same interface run_workload expects."""

    def __init__(self, short: Driver, long: Driver, long_ratio: float, rng: random.Random):
        self.short, self.long, self.long_ratio = short, long, long_ratio
        self._rng = rng
        self._lock = threading.Lock()

    def run_once(self, rng: random.Random, t0: float) -> Result:
        with self._lock:
            pick_long = self._rng.random() < self.long_ratio
        return (self.long if pick_long else self.short).run_once(rng, t0)


def cmd_failover(args: argparse.Namespace) -> int:
    """Inject a dead endpoint and prove the breaker parks it.

    Two failure shapes, because they hit different code paths: `refuse` is an
    instant ECONNREFUSED (APIConnectionError), `hang` accepts the TCP connection
    and never answers — the black-hole case the router's aggressive connect
    timeout and 120s read timeout exist for.
    """
    import socket  # noqa: PLC0415 - only this command needs raw sockets

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    hang_thread: threading.Thread | None = None
    accepted: list[socket.socket] = []
    stop_hang = threading.Event()

    if args.blackhole_mode == "hang":
        sock.listen(128)

        def accept_loop() -> None:
            sock.settimeout(0.5)
            while not stop_hang.is_set():
                try:
                    conn, _ = sock.accept()
                except OSError:
                    continue
                conn.setblocking(False)
                accepted.append(conn)  # accepted, never answered

        hang_thread = threading.Thread(target=accept_loop, name="blackhole", daemon=True)
        hang_thread.start()
        if args.read_timeout is None:
            # Without this every request that lands on the hang node waits the
            # router's 120s default and the run never finishes.
            args.read_timeout = 10.0
    else:
        sock.close()  # nothing listening → connections are refused

    dead = f"http://127.0.0.1:{port}/v1"
    base_endpoints = args.endpoints or os.getenv("VLLM_ENDPOINTS") or os.getenv("VLLM_ENDPOINT", "")
    if not base_endpoints:
        sys.exit("failover needs a live pool: pass --endpoints or --env-file")
    args.endpoints = f"{dead},{base_endpoints}" if args.dead_first else f"{base_endpoints},{dead}"

    router, nodes = bootstrap(args)
    workload = make_workload(args, router)
    driver = Driver(router, workload, args)
    live_nodes = [n for n in nodes if n != dead]
    print(f"failover: blackhole {dead} ({args.blackhole_mode}) + {len(live_nodes)} live node(s)")
    check_scale(args.concurrency, router)
    print()

    breaker_log: list[tuple[float, bool]] = []
    stop_watch = threading.Event()
    t_watch = time.perf_counter()

    def watch() -> None:
        last: bool | None = None
        while not stop_watch.wait(0.5):
            try:
                state = bool(router.stats().get(dead, {}).get("cooling_down"))
            except Exception:  # noqa: BLE001
                continue
            if state != last:
                breaker_log.append((time.perf_counter() - t_watch, state))
                last = state

    watcher = threading.Thread(target=watch, name="breaker-watch", daemon=True)
    watcher.start()
    try:
        outcome = run_workload(driver, args.concurrency, duration=args.duration,
                               seed=args.seed, progress_every=args.progress_interval,
                               label="failover")
    finally:
        stop_watch.set()
        watcher.join(timeout=2)
        stop_hang.set()
        if hang_thread is not None:
            hang_thread.join(timeout=2)
            for conn in accepted:
                try:
                    conn.close()
                except OSError:
                    pass
            try:
                sock.close()
            except OSError:
                pass

    s = summarise(outcome)
    touched = [r for r in outcome.results if dead in r.attempts]
    clean = [r for r in outcome.results if dead not in r.attempts and r.ok]
    recovered = [r for r in touched if r.ok]

    print("\n" + "=" * 78)
    print("FAILOVER")
    print("=" * 78)
    print(f"requests {s['requests']}  ok {s['ok']} ({100 * (1 - s['error_rate']):.2f}%)  "
          f"failover attempts {s['failovers']}")
    print(f"requests that hit the dead node: {len(touched)} "
          f"({100 * len(touched) / max(1, s['requests']):.1f}%), of which "
          f"{len(recovered)} recovered on another node")
    if touched and clean:
        penalty = pct([r.total for r in recovered], 50) - pct([r.total for r in clean], 50)
        print(f"median latency penalty for a failed-over request: {penalty * 1000:.0f}ms")

    # The dead node has 0 in-flight, so without the breaker it looks "least
    # loaded" and gets picked FIRST every time — decaying attempts over the run
    # is the observable proof the breaker is doing its job.
    half = outcome.wall / 2
    early = sum(1 for r in touched if r.t < half)
    late = sum(1 for r in touched if r.t >= half)
    print(f"attempts on the dead node: {early} in the first half, {late} in the second "
          f"({'decaying — breaker is parking it' if late <= early else 'NOT decaying — check the breaker'})")
    print(f"breaker transitions: "
          + (", ".join(f"{'park' if state else 'unpark'}@{t:.1f}s" for t, state in breaker_log)
             or "none observed"))
    print("\nPer-node share")
    for node, e in s["nodes"].items():
        tag = "  ← blackhole" if node == dead else ""
        print(f"  {_short(node):<42}{e['requests']:>10}{100 * e['share']:>7.1f}%{tag}")
    if s["errors"]:
        print(f"\nerrors: {s['errors']}")

    write_json(args, {"failover": s, "dead_node": dead,
                      "breaker_transitions": breaker_log,
                      "hit_dead": len(touched), "recovered": len(recovered)})
    ok_rate = 1 - s["error_rate"]
    failed = ok_rate < args.min_success_rate or late > early
    print(f"\nverdict: {'PASS' if not failed else 'FAIL'} "
          f"(success {100 * ok_rate:.1f}%, floor {100 * args.min_success_rate:.0f}%)")
    return 1 if failed else 0


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--endpoints", help="comma-separated vLLM base URLs "
                                            "(default: VLLM_ENDPOINTS from the environment)")
    common.add_argument("--env-file", help="file of KEY=VALUE lines to load first "
                                           "(e.g. .github/deploy/.env.prod)")
    common.add_argument("--model", help="override VLLM_MODEL")
    common.add_argument("--json", help="write the machine-readable report here")
    common.add_argument("--seed", type=int, default=7)
    common.add_argument("--connect-timeout", type=float, help="VLLM_CONNECT_TIMEOUT")
    common.add_argument("--read-timeout", type=float, help="VLLM_READ_TIMEOUT")
    common.add_argument("--breaker-threshold", type=int, help="VLLM_BREAKER_THRESHOLD")
    common.add_argument("--breaker-cooldown", type=float, help="VLLM_BREAKER_COOLDOWN")
    common.add_argument("--max-connections", type=int, help="VLLM_MAX_CONNECTIONS")
    common.add_argument("--max-keepalive", type=int, help="VLLM_MAX_KEEPALIVE")
    common.add_argument("--queue-aware", dest="queue_aware", action="store_true", default=None,
                        help="force VLLM_QUEUE_AWARE=1")
    common.add_argument("--no-queue-aware", dest="queue_aware", action="store_false",
                        help="force VLLM_QUEUE_AWARE=0 (compare routing with/without)")

    work = argparse.ArgumentParser(add_help=False)
    work.add_argument("--via", choices=("router", "direct"), default="router",
                      help="drive through InferenceRouter (default) or one endpoint directly")
    work.add_argument("--endpoint", help="--via direct target (default: first endpoint)")
    work.add_argument("--prompt-tokens", type=int, default=5000,
                      help="approximate prompt size; 5000 matches a real RAG ask")
    work.add_argument("--max-tokens", type=int, default=512)
    work.add_argument("--temperature", type=float, default=0.7)
    work.add_argument("--no-stream", action="store_true", help="disable streaming (no TTFT)")
    work.add_argument("--thinking", action="store_true",
                      help="allow the model's <think> preamble (off by default, as in prod)")
    work.add_argument("--shared-prefix", action="store_true",
                      help="reuse one prompt prefix so vLLM prefix caching applies")
    work.add_argument("--max-retries", type=int, default=5, help="call_with_rotation retry budget")
    work.add_argument("--retry-delay", type=float, default=2.0)
    work.add_argument("--sample-interval", type=float, default=1.0, help="/metrics poll interval")
    work.add_argument("--progress-interval", type=float, default=5.0, help="0 disables progress")
    work.add_argument("--max-error-rate", type=float, default=0.02)

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_nodes = sub.add_parser("nodes", parents=[common], help="inventory + health of the pool")
    p_nodes.add_argument("--probe-timeout", type=float, default=5.0)
    p_nodes.add_argument("--strict", action="store_true", help="exit 1 on any problem")
    p_nodes.set_defaults(func=cmd_nodes)

    p_sweep = sub.add_parser("sweep", parents=[common, work],
                             help="concurrency sweep → knee → sizing numbers")
    p_sweep.add_argument("--levels", default="1,2,4,8,16,24,32,48")
    p_sweep.add_argument("--requests-per-level", type=int,
                         help="default: max(2×concurrency, 12)")
    p_sweep.add_argument("--warmup", type=int, default=2)
    p_sweep.add_argument("--settle", type=float, default=5.0, help="pause between levels")
    p_sweep.add_argument("--ttft-slo-ms", type=float, default=3000.0)
    p_sweep.add_argument("--api-replicas", type=int, default=1)
    p_sweep.add_argument("--backend-workers", type=int, default=2)
    p_sweep.set_defaults(func=cmd_sweep)

    p_soak = sub.add_parser("soak", parents=[common, work], help="sustained load")
    p_soak.add_argument("--concurrency", type=int, default=24,
                        help="concurrent generations in flight (1000 is supported; "
                             "raise --max-connections to match)")
    p_soak.add_argument("--duration", type=float,
                        help="seconds (default 300 unless --requests is given)")
    p_soak.add_argument("--requests", type=int,
                        help="stop after this many requests, e.g. 1000")
    p_soak.set_defaults(func=cmd_soak)

    p_balance = sub.add_parser("balance", parents=[common, work],
                               help="routing fairness under a mixed workload")
    p_balance.add_argument("--concurrency", type=int, default=16)
    p_balance.add_argument("--requests", type=int, default=120)
    p_balance.add_argument("--long-ratio", type=float, default=0.25)
    p_balance.add_argument("--long-factor", type=int, default=4,
                           help="max_tokens multiplier for the long slice")
    p_balance.add_argument("--skew-tolerance", type=float, default=0.15,
                           help="max share deviation from an even split, as a fraction")
    p_balance.set_defaults(func=cmd_balance)

    p_fail = sub.add_parser("failover", parents=[common, work],
                            help="inject a dead endpoint, verify the breaker")
    p_fail.add_argument("--concurrency", type=int, default=8)
    p_fail.add_argument("--duration", type=float, default=60.0)
    p_fail.add_argument("--blackhole-mode", choices=("refuse", "hang"), default="refuse")
    p_fail.add_argument("--dead-first", action="store_true",
                        help="put the dead endpoint first in VLLM_ENDPOINTS")
    p_fail.add_argument("--min-success-rate", type=float, default=0.99)
    p_fail.set_defaults(func=cmd_failover)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
