#!/usr/bin/env python3
#AURA edge (nginx) load generator and shed-semantics probe.
 
from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import ssl
import statistics
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Sequence

try:
    import httpx
except ImportError:  # pragma: no cover - environment guard
    sys.exit("httpx is required. Use server/.venv/bin/python, or: pip install httpx")


# ── Workload definition ──────────────────────────────────────────────────────

DEFAULT_QUESTIONS = [
    "What is the fee structure for B.Tech ICT?",
    "When do the winter semester exams start?",
    "How many credits do I need to graduate from the B.Tech CS AI programme?",
    "Who is the Dean of Academic Affairs?",
    "What is the hostel curfew policy for first year students?",
    "Tell me about the summer research internship programme at DAU.",
    "What are the placement statistics for the last academic year?",
    "How do I apply for a scholarship as a second year student?",
    "What is the attendance requirement to sit for an end semester exam?",
    "Which electives are offered in the winter semester for ICT students?",
    "How do I get a bonafide certificate from the registrar's office?",
    "What are the library timings during the exam period?",
    "Explain the grading policy and how CGPA is computed at DAU.",
    "Is there a bus service between the campus and Gandhinagar city?",
    "What clubs can a first year student join and how do I sign up?",
]


@dataclass(frozen=True)
class Scenario:
    name: str
    method: str
    path: str
    sse: bool = False
    needs_jwt: bool = False
    note: str = ""


SCENARIOS: dict[str, Scenario] = {
    s.name: s
    for s in (
        Scenario("chat", "POST", "/api/chat", sse=True,
                 note="RAG/LLM via Next BFF — aura_chat_total/aura_chat_conn/aura_chat"),
        Scenario("page", "GET", "/", note="catch-all → Next.js, zone aura_api"),
        Scenario("static", "GET", "/manifest.json", note="static asset via catch-all"),
        Scenario("health", "GET", "/backend/health", note="FastAPI direct, zone aura_api"),
        Scenario("session", "GET", "/api/auth/session", note="zone aura_auth (5r/s)"),
        Scenario("backend_chat", "POST", "/backend/chat/stream", sse=True, needs_jwt=True,
                 note="bypasses Next BFF — needs --jwt-secret"),
    )
}

# Outcome taxonomy. Everything the run does lands in exactly one of these, and
# the report is organised around the shed-attribution subset.
OK = "ok"
EDGE_SHED = "edge_shed"                # nginx limit_req/limit_conn
BACKEND_QUOTA = "backend_quota"        # per-identity daily quota (429)
BACKEND_ADMISSION = "backend_admission"  # chat_queue_lock timeout (503)
PIPELINE_ERROR = "pipeline_error"      # RAG_PIPELINE_ERROR (503)
UPSTREAM_ERROR = "upstream_error"      # 502/504 — nginx could not reach/await upstream
HTTP_ERROR = "http_error"              # any other non-2xx
TIMEOUT = "timeout"
CONN_ERROR = "conn_error"
HARNESS_DROP = "harness_drop"          # open loop hit --max-inflight: our limit, not theirs

SHED_OUTCOMES = (EDGE_SHED, BACKEND_QUOTA, BACKEND_ADMISSION)
ERROR_OUTCOMES = (PIPELINE_ERROR, UPSTREAM_ERROR, HTTP_ERROR, TIMEOUT, CONN_ERROR)


# ── Small helpers ────────────────────────────────────────────────────────────

def pct(values: Sequence[float], p: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = (len(ordered) - 1) * (p / 100.0)
    lo, hi = math.floor(k), math.ceil(k)
    if lo == hi:
        return ordered[int(k)]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (k - lo)


def ms(value: float | None) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "-"
    return f"{value * 1000:.0f}"


def human_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024 or unit == "GB":
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}GB"


def parse_mix(raw: str) -> dict[str, float]:
    mix: dict[str, float] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise argparse.ArgumentTypeError(f"bad mix entry {part!r}, expected name=weight")
        name, _, weight = part.partition("=")
        name = name.strip()
        if name not in SCENARIOS:
            raise argparse.ArgumentTypeError(
                f"unknown scenario {name!r}; known: {', '.join(SCENARIOS)}"
            )
        try:
            mix[name] = float(weight)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"bad weight in {part!r}") from exc
    if not mix or sum(mix.values()) <= 0:
        raise argparse.ArgumentTypeError("mix must contain at least one positive weight")
    return mix


def ensure_fd_headroom(needed: int) -> str:
    """Raise RLIMIT_NOFILE toward the hard limit for high-concurrency runs.

    A 1000-VU run needs ~1000 sockets plus overhead, and macOS ships a soft
    limit of 256 — without this the harness fails with "Too many open files"
    and the result looks like a server error.
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
    if soft < want:
        return (f"fd limit: raised to {soft}, still below ~{want} — "
                f"expect 'Too many open files' at this concurrency")
    return f"fd limit: raised to {soft}"


class JwtMinter:
    """Mints the internal Next→FastAPI JWT so /backend/* can be driven directly.

    Claims and iss/aud must match aura/lib/auth/internal-jwt.ts; the token is
    short-lived, so it is re-minted well before the 15m expiry.
    """

    def __init__(self, secret: str, role: str, erp_id: str | None):
        try:
            import jwt  # noqa: PLC0415 - optional dependency, only for --jwt-secret
        except ImportError:  # pragma: no cover - environment guard
            sys.exit("--jwt-secret needs PyJWT: pip install pyjwt")
        self._jwt = jwt
        self._secret = secret
        self._role = role
        self._erp_id = erp_id or f"LOADTEST-{uuid.uuid4().hex[:12]}"
        self._token = ""
        self._minted_at = 0.0

    def token(self) -> str:
        now = time.time()
        if not self._token or now - self._minted_at > 300:
            self._token = self._jwt.encode(
                {
                    "role": self._role,
                    "erpId": self._erp_id,
                    "email": None if self._role == "guest" else f"{self._erp_id}@dau.ac.in",
                    "iss": "aura-next",
                    "aud": "aura-api",
                    "exp": int(now) + 900,
                },
                self._secret,
                algorithm="HS256",
            )
            self._minted_at = now
        return self._token


# ── Sample collection ────────────────────────────────────────────────────────

@dataclass
class Sample:
    t: float                 # seconds since run start (request start)
    scenario: str
    outcome: str
    status: int | None
    ttfb: float | None
    ttft: float | None       # first SSE text-delta
    total: float
    nbytes: int
    deltas: int
    max_gap: float | None    # largest inter-delta gap, the SSE stall signal
    detail: str = ""


@dataclass
class Bucket:
    n: int = 0
    ok: int = 0
    shed: int = 0
    err: int = 0
    lat: list[float] = field(default_factory=list)


class Recorder:
    def __init__(self, bucket_seconds: float, budget: int | None = None):
        self.samples: list[Sample] = []
        self.buckets: dict[int, Bucket] = {}
        self.bucket_seconds = bucket_seconds
        self.inflight = 0
        self.started = 0
        self.t0 = time.perf_counter()
        self._last_report = (0, 0.0)
        # Total-request budget (--requests). The drivers run on one event loop,
        # so a plain counter is atomic enough — no lock needed.
        self.remaining = budget

    def take(self) -> bool:
        """Claim one request from the budget. False once it is spent."""
        if self.remaining is None:
            return True
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True

    def add(self, s: Sample) -> None:
        self.samples.append(s)
        idx = int(s.t // self.bucket_seconds)
        bucket = self.buckets.setdefault(idx, Bucket())
        bucket.n += 1
        bucket.lat.append(s.total)
        if s.outcome == OK:
            bucket.ok += 1
        elif s.outcome in SHED_OUTCOMES:
            bucket.shed += 1
        elif s.outcome != HARNESS_DROP:
            bucket.err += 1

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for s in self.samples:
            out[s.outcome] = out.get(s.outcome, 0) + 1
        return out

    def since_last(self) -> tuple[int, float]:
        n, t = len(self.samples), time.perf_counter()
        prev_n, prev_t = self._last_report
        self._last_report = (n, t)
        return n - prev_n, max(1e-6, t - prev_t)


# ── HTTP execution ───────────────────────────────────────────────────────────

@dataclass
class Config:
    target: str
    scenarios: dict[str, float]
    insecure: bool
    http2: bool
    host_header: str | None
    connect_timeout: float
    read_timeout: float
    sticky_cookies: bool
    history_turns: int
    questions: list[str]
    minter: JwtMinter | None
    user_agent: str

    def scenario_names(self) -> list[str]:
        return list(self.scenarios)

    def weights(self) -> list[float]:
        return list(self.scenarios.values())


def make_client(cfg: Config, max_conns: int = 1) -> httpx.AsyncClient:
    headers = {"User-Agent": cfg.user_agent, "Accept-Encoding": "gzip"}
    if cfg.host_header:
        headers["Host"] = cfg.host_header
    verify: Any = False if cfg.insecure else True
    kwargs: dict[str, Any] = dict(
        base_url=cfg.target,
        headers=headers,
        verify=verify,
        follow_redirects=False,
        limits=httpx.Limits(max_connections=max_conns, max_keepalive_connections=max_conns),
        timeout=httpx.Timeout(
            connect=cfg.connect_timeout,
            read=cfg.read_timeout,
            write=30.0,
            pool=cfg.read_timeout,
        ),
    )
    if cfg.http2:
        kwargs["http2"] = True
    return httpx.AsyncClient(**kwargs)


def build_chat_body(cfg: Config, rng: random.Random) -> bytes:
    question = rng.choice(cfg.questions)
    history = []
    for i in range(cfg.history_turns):
        history.append({"role": "user" if i % 2 == 0 else "assistant",
                        "content": rng.choice(cfg.questions)})
    payload: dict[str, Any] = {
        "question": question,
        "threadId": uuid.uuid4().hex[:32],
    }
    if history:
        payload["history"] = history
    return json.dumps(payload).encode()


def classify(status: int, headers: httpx.Headers, body: bytes) -> tuple[str, str]:
    """Map an HTTP response onto the shed taxonomy.

    nginx runs with proxy_intercept_errors off, so an upstream 429/503 reaches
    us verbatim while an edge shed carries X-Aura-Shed-By/EDGE_OVERLOADED —
    that is exactly what separates "the edge shed it" from "the backend did".
    """
    text = body[:512].decode("utf-8", "replace")
    if 200 <= status < 300:
        return OK, ""
    if status == 429:
        if headers.get("x-aura-shed-by") == "edge" or "EDGE_OVERLOADED" in text:
            return EDGE_SHED, f"retry-after={headers.get('retry-after', '-')}"
        return BACKEND_QUOTA, text.strip()[:120]
    if status == 503:
        if "RAG_PIPELINE_ERROR" in text:
            return PIPELINE_ERROR, text.strip()[:120]
        return BACKEND_ADMISSION, f"retry-after={headers.get('retry-after', '-')}"
    if status in (502, 504):
        return UPSTREAM_ERROR, f"status={status}"
    return HTTP_ERROR, f"status={status} {text.strip()[:100]}"


async def execute(client: httpx.AsyncClient, scen: Scenario, cfg: Config,
                  rng: random.Random, t_run: float) -> Sample:
    started = time.perf_counter()
    headers: dict[str, str] = {}
    content: bytes | None = None
    if scen.sse:
        content = build_chat_body(cfg, rng)
        headers["Content-Type"] = "application/json"
        headers["Accept"] = "text/event-stream"
    if scen.needs_jwt and cfg.minter is not None:
        headers["Authorization"] = f"Bearer {cfg.minter.token()}"

    ttfb = ttft = None
    nbytes = deltas = 0
    max_gap = 0.0
    last_delta: float | None = None
    try:
        async with client.stream(scen.method, scen.path, content=content,
                                 headers=headers) as resp:
            ttfb = time.perf_counter() - started
            if resp.status_code != 200:
                raw = await resp.aread()
                outcome, detail = classify(resp.status_code, resp.headers, raw)
                return Sample(t_run, scen.name, outcome, resp.status_code, ttfb, None,
                              time.perf_counter() - started, len(raw), 0, None, detail)
            async for chunk in resp.aiter_bytes():
                nbytes += len(chunk)
                if not scen.sse:
                    continue
                hits = chunk.count(b'"text-delta"')
                if hits:
                    now = time.perf_counter()
                    if ttft is None:
                        ttft = now - started
                    elif last_delta is not None:
                        max_gap = max(max_gap, now - last_delta)
                    last_delta = now
                    deltas += hits
            outcome, detail = OK, ""
            if scen.sse and deltas == 0:
                # 200 with no answer tokens is a silent failure — the SSE error
                # event path. Do not let it count as a success.
                outcome, detail = HTTP_ERROR, "200 but no text-delta events"
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as exc:
        return Sample(t_run, scen.name, TIMEOUT, None, ttfb, ttft,
                      time.perf_counter() - started, nbytes, deltas, None,
                      type(exc).__name__)
    except (httpx.HTTPError, ssl.SSLError, OSError) as exc:
        return Sample(t_run, scen.name, CONN_ERROR, None, ttfb, ttft,
                      time.perf_counter() - started, nbytes, deltas, None,
                      f"{type(exc).__name__}: {exc}"[:140])
    finally:
        if not cfg.sticky_cookies:
            client.cookies.clear()

    return Sample(t_run, scen.name, outcome, 200, ttfb, ttft,
                  time.perf_counter() - started, nbytes, deltas,
                  max_gap if deltas > 1 else None, detail)


async def run_one(client: httpx.AsyncClient, scen: Scenario, cfg: Config,
                  rng: random.Random, rec: Recorder) -> None:
    rec.inflight += 1
    rec.started += 1
    try:
        sample = await execute(client, scen, cfg, rng, time.perf_counter() - rec.t0)
        rec.add(sample)
    finally:
        rec.inflight -= 1


# ── Load shaping ─────────────────────────────────────────────────────────────

@dataclass
class Shape:
    duration: float
    ramp: float
    spike_at: float | None
    spike_factor: float
    spike_duration: float

    def factor(self, elapsed: float) -> float:
        """Multiplier on the target load at `elapsed` seconds into the run."""
        f = 1.0 if self.ramp <= 0 else min(1.0, elapsed / self.ramp)
        if self.spike_at is not None and self.spike_at <= elapsed < self.spike_at + self.spike_duration:
            f *= self.spike_factor
        return f


async def closed_loop(cfg: Config, shape: Shape, rec: Recorder, vus: int,
                      think_time: float, seed: int) -> None:
    """`vus` virtual users, each holding its own connection and looping.

    One client per VU (max_connections=1) so the run maps onto nginx's
    limit_conn accounting the way N real browsers would.
    """
    stop_at = rec.t0 + shape.duration
    names, weights = cfg.scenario_names(), cfg.weights()

    async def vu(idx: int) -> None:
        rng = random.Random(seed + idx)
        # Stagger VU start across the ramp instead of a synchronised stampede.
        if shape.ramp > 0:
            await asyncio.sleep(shape.ramp * idx / max(1, vus))
        client = make_client(cfg, max_conns=1)
        try:
            while time.perf_counter() < stop_at and rec.take():
                scen = SCENARIOS[rng.choices(names, weights=weights, k=1)[0]]
                await run_one(client, scen, cfg, rng, rec)
                if think_time > 0:
                    await asyncio.sleep(rng.uniform(0, 2 * think_time))
        finally:
            await client.aclose()

    await asyncio.gather(*(vu(i) for i in range(vus)), return_exceptions=True)


async def open_loop(cfg: Config, shape: Shape, rec: Recorder, rate: float,
                    max_inflight: int, conn_pool: int, poisson: bool,
                    seed: int) -> None:
    """Arrivals independent of completions — the only way to observe real
    shedding. A closed loop self-throttles as the server slows down, which
    hides exactly the overload behaviour this edge is built for."""
    rng = random.Random(seed)
    # Spread max_inflight across the client pool: a client whose pool is full
    # would queue the next request instead of opening a connection, which would
    # measure OUR pool wait rather than the edge's admission behaviour.
    per_client = max(1, math.ceil(max_inflight / max(1, conn_pool)))
    clients = [make_client(cfg, max_conns=per_client) for _ in range(conn_pool)]
    names, weights = cfg.scenario_names(), cfg.weights()
    tasks: set[asyncio.Task[None]] = set()
    stop_at = rec.t0 + shape.duration
    cursor = 0
    try:
        while True:
            now = time.perf_counter()
            if now >= stop_at:
                break
            current = rate * shape.factor(now - rec.t0)
            if current <= 0:
                await asyncio.sleep(0.05)
                continue
            gap = rng.expovariate(current) if poisson else 1.0 / current
            await asyncio.sleep(gap)
            if rec.inflight >= max_inflight:
                rec.add(Sample(time.perf_counter() - rec.t0, "-", HARNESS_DROP, None,
                               None, None, 0.0, 0, 0, None, "max-inflight reached"))
                continue
            if not rec.take():
                break
            scen = SCENARIOS[rng.choices(names, weights=weights, k=1)[0]]
            client = clients[cursor % len(clients)]
            cursor += 1
            task = asyncio.create_task(run_one(client, scen, cfg, rng, rec))
            tasks.add(task)
            task.add_done_callback(tasks.discard)
        if tasks:
            await asyncio.wait(tasks, timeout=cfg.read_timeout + 5)
    finally:
        for client in clients:
            await client.aclose()


async def progress(rec: Recorder, interval: float, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
            return
        except asyncio.TimeoutError:
            pass
        n, dt = rec.since_last()
        window = [s.total for s in rec.samples[-n:]] if n > 0 else []
        counts = rec.counts()
        shed = sum(counts.get(k, 0) for k in SHED_OUTCOMES)
        err = sum(counts.get(k, 0) for k in ERROR_OUTCOMES)
        print(
            f"[{time.perf_counter() - rec.t0:6.1f}s] "
            f"rps={n / dt:7.1f} inflight={rec.inflight:5d} done={len(rec.samples):7d} "
            f"p95={ms(pct(window, 95)):>7}ms shed={shed:5d} err={err:5d}",
            flush=True,
        )


# ── Reporting ────────────────────────────────────────────────────────────────

def build_report(rec: Recorder, cfg: Config, meta: dict[str, Any]) -> dict[str, Any]:
    samples = rec.samples
    real = [s for s in samples if s.outcome != HARNESS_DROP]
    counts = rec.counts()
    wall = max(1e-6, time.perf_counter() - rec.t0)
    ok = [s for s in real if s.outcome == OK]
    shed = sum(counts.get(k, 0) for k in SHED_OUTCOMES)
    err = sum(counts.get(k, 0) for k in ERROR_OUTCOMES)

    per_scenario: dict[str, Any] = {}
    for name in sorted({s.scenario for s in real}):
        rows = [s for s in real if s.scenario == name]
        lat = [s.total for s in rows if s.outcome == OK]
        ttfbs = [s.ttfb for s in rows if s.ttfb is not None]
        entry: dict[str, Any] = {
            "requests": len(rows),
            "ok": sum(1 for s in rows if s.outcome == OK),
            "latency_ms": {f"p{p}": pct(lat, p) * 1000 for p in (50, 90, 95, 99)} if lat else {},
            "latency_max_ms": (max(lat) * 1000) if lat else None,
            "ttfb_p95_ms": pct(ttfbs, 95) * 1000 if ttfbs else None,
        }
        ttfts = [s.ttft for s in rows if s.ttft is not None]
        if ttfts:
            entry["ttft_ms"] = {f"p{p}": pct(ttfts, p) * 1000 for p in (50, 90, 95, 99)}
            deltas = [s.deltas for s in rows if s.deltas]
            gaps = [s.max_gap for s in rows if s.max_gap is not None]
            entry["sse"] = {
                "streams": len(ttfts),
                "deltas_mean": statistics.fmean(deltas) if deltas else 0,
                "max_inter_delta_gap_ms": (max(gaps) * 1000) if gaps else None,
            }
        per_scenario[name] = entry

    timeline = []
    for idx in sorted(rec.buckets):
        b = rec.buckets[idx]
        timeline.append({
            "t": idx * rec.bucket_seconds,
            "rps": b.n / rec.bucket_seconds,
            "ok": b.ok,
            "shed": b.shed,
            "err": b.err,
            "p95_ms": pct(b.lat, 95) * 1000,
        })

    details: dict[str, int] = {}
    for s in real:
        if s.outcome in ERROR_OUTCOMES and s.detail:
            details[f"{s.outcome}: {s.detail}"] = details.get(f"{s.outcome}: {s.detail}", 0) + 1

    return {
        "meta": meta,
        "totals": {
            "requests": len(real),
            "harness_drops": counts.get(HARNESS_DROP, 0),
            "ok": len(ok),
            "shed": shed,
            "errors": err,
            "wall_seconds": wall,
            "throughput_rps": len(real) / wall,
            "bytes": sum(s.nbytes for s in real),
            "error_rate": (err / len(real)) if real else 0.0,
            "shed_rate": (shed / len(real)) if real else 0.0,
        },
        "outcomes": counts,
        "status_codes": _status_histogram(real),
        "scenarios": per_scenario,
        "timeline": timeline,
        "error_details": dict(sorted(details.items(), key=lambda kv: -kv[1])[:12]),
    }


def _status_histogram(samples: list[Sample]) -> dict[str, int]:
    hist: dict[str, int] = {}
    for s in samples:
        key = str(s.status) if s.status is not None else "(no response)"
        hist[key] = hist.get(key, 0) + 1
    return dict(sorted(hist.items()))


def print_report(report: dict[str, Any]) -> None:
    meta, tot = report["meta"], report["totals"]
    print("\n" + "=" * 78)
    print("AURA EDGE LOAD TEST — " + meta["target"])
    print("=" * 78)
    for key in ("mode", "shape", "mix", "transport"):
        if meta.get(key):
            print(f"{key:<12} {meta[key]}")
    print(f"{'wall':<12} {tot['wall_seconds']:.1f}s")
    print(
        f"\nrequests {tot['requests']:,}  ok {tot['ok']:,} "
        f"({100 * tot['ok'] / max(1, tot['requests']):.1f}%)  "
        f"throughput {tot['throughput_rps']:.1f} rps  transferred {human_bytes(tot['bytes'])}"
    )
    if tot["harness_drops"]:
        print(f"WARNING: {tot['harness_drops']:,} arrivals dropped by the HARNESS "
              f"(--max-inflight) — raise it or the offered load is understated.")

    print("\nStatus codes: " + "  ".join(f"{k}×{v:,}" for k, v in report["status_codes"].items()))

    print("\nShed attribution")
    print(f"  {'outcome':<22}{'count':>10}{'share':>9}")
    total = max(1, tot["requests"])
    for outcome in (OK, EDGE_SHED, BACKEND_QUOTA, BACKEND_ADMISSION, PIPELINE_ERROR,
                    UPSTREAM_ERROR, HTTP_ERROR, TIMEOUT, CONN_ERROR):
        n = report["outcomes"].get(outcome, 0)
        if n:
            print(f"  {outcome:<22}{n:>10,}{100 * n / total:>8.1f}%")

    print("\nLatency by scenario (ms)")
    print(f"  {'scenario':<14}{'n':>8}{'ok':>8}{'p50':>8}{'p90':>8}{'p95':>8}{'p99':>8}{'max':>9}{'ttfb p95':>10}")
    for name, entry in report["scenarios"].items():
        lat = entry["latency_ms"]
        print(
            f"  {name:<14}{entry['requests']:>8,}{entry['ok']:>8,}"
            f"{_g(lat, 'p50'):>8}{_g(lat, 'p90'):>8}{_g(lat, 'p95'):>8}{_g(lat, 'p99'):>8}"
            f"{_n(entry['latency_max_ms']):>9}{_n(entry['ttfb_p95_ms']):>10}"
        )

    streams = {k: v for k, v in report["scenarios"].items() if "ttft_ms" in v}
    if streams:
        print("\nSSE streams")
        print(f"  {'scenario':<14}{'streams':>9}{'ttft p50':>10}{'ttft p95':>10}{'ttft p99':>10}"
              f"{'deltas/req':>12}{'max gap':>10}")
        for name, entry in streams.items():
            t = entry.get("ttft_ms", {})
            sse = entry.get("sse", {})
            print(
                f"  {name:<14}{sse.get('streams', 0):>9,}{_g(t, 'p50'):>10}{_g(t, 'p95'):>10}"
                f"{_g(t, 'p99'):>10}{sse.get('deltas_mean', 0):>12.0f}"
                f"{_n(sse.get('max_inter_delta_gap_ms')):>10}"
            )

    timeline = report["timeline"]
    if len(timeline) > 1:
        print("\nTimeline")
        print(f"  {'t(s)':>6}{'rps':>9}{'ok':>8}{'shed':>8}{'err':>8}{'p95 ms':>9}")
        rows = timeline if len(timeline) <= 40 else timeline[:20] + timeline[-20:]
        for i, row in enumerate(rows):
            if len(timeline) > 40 and i == 20:
                print(f"  {'...':>6}")
            print(f"  {row['t']:>6.0f}{row['rps']:>9.1f}{row['ok']:>8,}{row['shed']:>8,}"
                  f"{row['err']:>8,}{row['p95_ms']:>9.0f}")

    if report["error_details"]:
        print("\nTop error details")
        for detail, n in report["error_details"].items():
            print(f"  {n:>6,}  {detail}")


def _g(d: dict[str, Any], key: str) -> str:
    v = d.get(key)
    return "-" if v is None else f"{v:.0f}"


def _n(v: Any) -> str:
    return "-" if v is None else f"{v:.0f}"


def evaluate_slos(report: dict[str, Any], args: argparse.Namespace) -> list[tuple[str, bool, str]]:
    results: list[tuple[str, bool, str]] = []
    tot = report["totals"]
    if args.slo_error_rate is not None:
        rate = tot["error_rate"]
        results.append(("error rate", rate <= args.slo_error_rate,
                        f"{100 * rate:.2f}% (limit {100 * args.slo_error_rate:.2f}%)"))
    if args.slo_shed_rate is not None:
        rate = tot["shed_rate"]
        results.append(("shed rate", rate <= args.slo_shed_rate,
                        f"{100 * rate:.2f}% (limit {100 * args.slo_shed_rate:.2f}%)"))
    if args.slo_p95_ms is not None:
        worst, name = 0.0, "-"
        for scen, entry in report["scenarios"].items():
            v = entry["latency_ms"].get("p95")
            if v and v > worst:
                worst, name = v, scen
        results.append((f"p95 latency ({name})", worst <= args.slo_p95_ms,
                        f"{worst:.0f}ms (limit {args.slo_p95_ms:.0f}ms)"))
    if args.slo_ttft_p95_ms is not None:
        worst, name = 0.0, "-"
        for scen, entry in report["scenarios"].items():
            v = entry.get("ttft_ms", {}).get("p95")
            if v and v > worst:
                worst, name = v, scen
        results.append((f"TTFT p95 ({name})", worst <= args.slo_ttft_p95_ms,
                        f"{worst:.0f}ms (limit {args.slo_ttft_p95_ms:.0f}ms)"))
    return results


# ── probe: edge semantics assertions ─────────────────────────────────────────

@dataclass
class Check:
    name: str
    status: str  # PASS | FAIL | WARN | SKIP
    detail: str


SECURITY_HEADERS = (
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "strict-transport-security",
    "permissions-policy",
)


async def probe(cfg: Config, args: argparse.Namespace) -> list[Check]:
    checks: list[Check] = []
    url = httpx.URL(cfg.target)
    client = make_client(cfg, max_conns=8)

    async def get(path: str, **kw: Any) -> httpx.Response | Exception:
        try:
            return await client.request("GET", path, **kw)
        except Exception as exc:  # noqa: BLE001 - probe reports the failure
            return exc

    try:
        # 1. HTTP → HTTPS redirect.
        if url.scheme == "https":
            plain = cfg.target.replace("https://", "http://", 1)
            try:
                async with make_client(Config(**{**cfg.__dict__, "target": plain}),
                                       max_conns=1) as c:
                    r = await c.get("/")
                    ok = r.status_code == 301 and r.headers.get("location", "").startswith("https://")
                    checks.append(Check("http→https redirect", "PASS" if ok else "FAIL",
                                        f"{r.status_code} → {r.headers.get('location', '-')}"))
            except Exception as exc:  # noqa: BLE001
                checks.append(Check("http→https redirect", "WARN", f"port 80 unreachable: {exc}"))
        else:
            checks.append(Check("http→https redirect", "SKIP", "target is plain http"))

        # 2. Security headers on a normal response.
        r = await get("/")
        if isinstance(r, Exception):
            checks.append(Check("security headers", "FAIL", str(r)))
        else:
            missing = [h for h in SECURITY_HEADERS if h not in r.headers]
            checks.append(Check("security headers on 200", "PASS" if not missing else "FAIL",
                                "all present" if not missing else f"missing {missing}"))
            server = r.headers.get("server", "")
            leaks = any(ch.isdigit() for ch in server)
            checks.append(Check("server_tokens off", "FAIL" if leaks else "PASS",
                                f"Server: {server or '(absent)'}"))

        # 3. Internal-only paths must not be reachable from the edge.
        for path in ("/backend/internal/resolve-identity", "/backend/metrics"):
            r = await get(path)
            if isinstance(r, Exception):
                checks.append(Check(f"hidden {path}", "FAIL", str(r)))
            else:
                checks.append(Check(f"hidden {path}", "PASS" if r.status_code == 404 else "FAIL",
                                    f"status {r.status_code} (want 404)"))

        # 4. large_client_header_buffers — a fat session cookie must not 400.
        big_cookie = "aura-loadtest=" + "x" * 12000
        r = await get("/", headers={"Cookie": big_cookie})
        if isinstance(r, Exception):
            checks.append(Check("12KB cookie accepted", "FAIL", str(r)))
        else:
            checks.append(Check("12KB cookie accepted", "PASS" if r.status_code != 400 else "FAIL",
                                f"status {r.status_code} (400 ⇒ header buffers too small)"))

        # 5. Body caps: /api/chat allows ~1m, oversize must 413 (not 400/502).
        for path, size, want_reject in (("/api/chat", 2_000_000, True),
                                        ("/api/chat", 400_000, False)):
            body = json.dumps({"question": "x" * (size - 64), "threadId": "probe"}).encode()
            try:
                r2 = await client.post(path, content=body,
                                       headers={"Content-Type": "application/json"})
                got = r2.status_code
                if want_reject:
                    ok = got == 413
                    detail = f"{size // 1000}KB → {got} (want 413)"
                else:
                    ok = got != 413
                    detail = f"{size // 1000}KB → {got} (must not be 413)"
                checks.append(Check(f"body cap {path} {size // 1000}KB",
                                    "PASS" if ok else "FAIL", detail))
            except Exception as exc:  # noqa: BLE001 - nginx may reset on oversize
                checks.append(Check(f"body cap {path} {size // 1000}KB",
                                    "WARN" if want_reject else "FAIL",
                                    f"connection error: {type(exc).__name__}"))

        # 6. SSE must reach the client unbuffered and uncompressed.
        try:
            async with client.stream("POST", "/api/chat",
                                     content=build_chat_body(cfg, random.Random(0)),
                                     headers={"Content-Type": "application/json",
                                              "Accept": "text/event-stream"}) as resp:
                ctype = resp.headers.get("content-type", "")
                enc = resp.headers.get("content-encoding", "")
                if resp.status_code != 200:
                    await resp.aread()
                    checks.append(Check("SSE pass-through", "WARN",
                                        f"chat returned {resp.status_code}; cannot assess streaming"))
                else:
                    ok = "text/event-stream" in ctype and not enc
                    checks.append(Check("SSE pass-through", "PASS" if ok else "FAIL",
                                        f"content-type={ctype!r} content-encoding={enc or 'none'!r}"))
                    await resp.aclose()
        except Exception as exc:  # noqa: BLE001
            checks.append(Check("SSE pass-through", "FAIL", f"{type(exc).__name__}: {exc}"))

        # 7. Edge shed shape: trip limit_req and inspect the 429 nginx renders.
        burst = args.probe_burst
        results = await asyncio.gather(*(get("/") for _ in range(burst)),
                                       return_exceptions=True)
        shed = [r for r in results if isinstance(r, httpx.Response) and r.status_code == 429]
        if not shed:
            checks.append(Check("edge shed triggers", "FAIL",
                                f"{burst} concurrent GET / produced no 429 — limit_req not active "
                                f"(is this really the nginx edge?)"))
        else:
            r = shed[0]
            body = r.text
            problems = []
            if r.headers.get("x-aura-shed-by") != "edge":
                problems.append("missing X-Aura-Shed-By: edge")
            if r.headers.get("retry-after") != "5":
                problems.append(f"Retry-After={r.headers.get('retry-after')!r}")
            if "EDGE_OVERLOADED" not in body:
                problems.append("body is not the @aura_shed JSON")
            checks.append(Check("edge shed shape", "PASS" if not problems else "FAIL",
                                f"{len(shed)}/{burst} shed; " +
                                ("as configured" if not problems else "; ".join(problems))))
            # add_header does not merge across levels — @aura_shed repeats them
            # by hand, and a future edit that drops one belongs in this report.
            missing = [h for h in SECURITY_HEADERS if h not in r.headers]
            checks.append(Check("security headers on 429", "PASS" if not missing else "FAIL",
                                "all present" if not missing else f"missing {missing}"))
    finally:
        await client.aclose()

    # 8. Slowloris: a stalled header write must be dropped near client_header_timeout.
    checks.append(await slowloris_check(cfg, args.slowloris_budget))
    return checks


async def slowloris_check(cfg: Config, budget: float) -> Check:
    url = httpx.URL(cfg.target)
    host = url.host
    port = url.port or (443 if url.scheme == "https" else 80)
    ctx = None
    if url.scheme == "https":
        ctx = ssl.create_default_context()
        if cfg.insecure:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port, ssl=ctx,
                                    server_hostname=host if ctx else None),
            timeout=10,
        )
    except Exception as exc:  # noqa: BLE001
        return Check("slowloris dropped", "FAIL", f"connect failed: {exc}")
    try:
        writer.write(f"GET / HTTP/1.1\r\nHost: {cfg.host_header or host}\r\n".encode())
        await writer.drain()

        async def dribble() -> None:
            while True:
                await asyncio.sleep(3)
                writer.write(b"X-Slow: 1\r\n")
                await writer.drain()

        drip = asyncio.create_task(dribble())
        try:
            data = await asyncio.wait_for(reader.read(256), timeout=budget)
        except asyncio.TimeoutError:
            return Check("slowloris dropped", "FAIL",
                         f"connection still open after {budget:.0f}s "
                         f"(client_header_timeout should close it ~12s)")
        finally:
            drip.cancel()
        elapsed = time.perf_counter() - started
        if not data:
            return Check("slowloris dropped", "PASS", f"connection closed after {elapsed:.1f}s")
        first = data.split(b"\r\n", 1)[0].decode("ascii", "replace")
        ok = b" 408 " in data or b" 400 " in data
        return Check("slowloris dropped", "PASS" if ok else "WARN",
                     f"{first} after {elapsed:.1f}s")
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:  # noqa: BLE001 - socket already gone
            pass


# ── Entrypoints ──────────────────────────────────────────────────────────────

def build_config(args: argparse.Namespace, mix: dict[str, float]) -> Config:
    questions = DEFAULT_QUESTIONS
    if getattr(args, "questions", None):
        with open(args.questions, encoding="utf-8") as fh:
            questions = [ln.strip() for ln in fh if ln.strip()]
        if not questions:
            sys.exit(f"{args.questions} contained no questions")
    minter = None
    if getattr(args, "jwt_secret", None):
        minter = JwtMinter(args.jwt_secret, args.jwt_role, args.jwt_erp_id)
    needs_jwt = [n for n in mix if SCENARIOS[n].needs_jwt]
    if needs_jwt and minter is None:
        sys.exit(f"scenario(s) {needs_jwt} need --jwt-secret (INTERNAL_JWT_SECRET)")
    http2 = args.http2
    if http2:
        try:
            import h2  # noqa: F401, PLC0415 - availability probe
        except ImportError:
            print("h2 not installed — falling back to HTTP/1.1", file=sys.stderr)
            http2 = False
    return Config(
        target=args.target.rstrip("/"),
        scenarios=mix,
        insecure=args.insecure,
        http2=http2,
        host_header=args.host_header,
        connect_timeout=args.connect_timeout,
        read_timeout=args.read_timeout,
        sticky_cookies=getattr(args, "sticky_cookies", False),
        history_turns=getattr(args, "history_turns", 0),
        questions=questions,
        minter=minter,
        user_agent=args.user_agent,
    )


async def cmd_load(args: argparse.Namespace) -> int:
    mix = parse_mix(args.mix)
    cfg = build_config(args, mix)
    # With a request budget and no explicit duration, run until the budget is
    # spent rather than cutting the run off at the default 60s.
    args.duration = args.duration if args.duration is not None else (3600.0 if args.requests else 60.0)
    shape = Shape(args.duration, args.ramp, args.spike_at, args.spike_factor,
                  args.spike_duration)
    rec = Recorder(args.bucket, args.requests)

    mix_text = " ".join(f"{k}={v:g}" for k, v in mix.items())
    if args.rate:
        mode = f"open-loop {args.rate:g} req/s ({'poisson' if args.poisson else 'constant'} arrivals)"
        concurrency = args.max_inflight
    else:
        mode = f"closed-loop {args.vus} VUs"
        concurrency = args.vus
    if args.requests:
        mode += f", stopping after {args.requests:,} requests"
    shape_text = f"{args.duration:g}s duration, {args.ramp:g}s ramp"
    if args.spike_at is not None:
        shape_text += f", ×{args.spike_factor:g} spike at {args.spike_at:g}s for {args.spike_duration:g}s"
    transport = ("HTTP/2" if cfg.http2 else "HTTP/1.1") + (", TLS verify off" if cfg.insecure else "")
    print(f"target    {cfg.target}\nmode      {mode}\nshape     {shape_text}\n"
          f"mix       {mix_text}\ntransport {transport}\n"
          f"identity  {'sticky cookies (quota WILL bite)' if cfg.sticky_cookies else 'fresh guest per request'}\n"
          f"limits    {ensure_fd_headroom(concurrency)}\n")

    stop = asyncio.Event()
    prog = asyncio.create_task(progress(rec, args.progress_interval, stop))
    try:
        if args.rate:
            await open_loop(cfg, shape, rec, args.rate, args.max_inflight,
                            args.conn_pool or min(args.max_inflight, 256), args.poisson,
                            args.seed)
        else:
            await closed_loop(cfg, shape, rec, args.vus, args.think_time, args.seed)
    except KeyboardInterrupt:
        print("\ninterrupted — reporting what completed so far", file=sys.stderr)
    finally:
        stop.set()
        await asyncio.gather(prog, return_exceptions=True)

    if not rec.samples:
        print("no requests completed", file=sys.stderr)
        return 2
    report = build_report(rec, cfg, {
        "target": cfg.target, "mode": mode, "shape": shape_text,
        "mix": mix_text, "transport": transport,
    })
    print_report(report)

    slos = evaluate_slos(report, args)
    failed = False
    if slos:
        print("\nSLOs")
        for name, ok, detail in slos:
            print(f"  {'PASS' if ok else 'FAIL'}  {name:<26} {detail}")
            failed |= not ok
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
        print(f"\nJSON report → {args.json}")
    if args.csv:
        with open(args.csv, "w", encoding="utf-8") as fh:
            fh.write("t,scenario,outcome,status,ttfb_ms,ttft_ms,total_ms,bytes,deltas\n")
            for s in rec.samples:
                fh.write(f"{s.t:.4f},{s.scenario},{s.outcome},{s.status or ''},"
                         f"{'' if s.ttfb is None else s.ttfb * 1000:.1f},"
                         f"{'' if s.ttft is None else s.ttft * 1000:.1f},"
                         f"{s.total * 1000:.1f},{s.nbytes},{s.deltas}\n")
        print(f"raw samples → {args.csv}")
    return 1 if failed else 0


async def cmd_probe(args: argparse.Namespace) -> int:
    cfg = build_config(args, {"page": 1})
    print(f"probing {cfg.target} — this deliberately trips rate limits\n")
    checks = await probe(cfg, args)
    width = max(len(c.name) for c in checks)
    failures = 0
    for c in checks:
        print(f"  {c.status:<5} {c.name:<{width}}  {c.detail}")
        failures += c.status == "FAIL"
    print(f"\n{len(checks)} checks, {failures} failed")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump([c.__dict__ for c in checks], fh, indent=2)
        print(f"JSON report → {args.json}")
    return 1 if failures else 0


async def cmd_smoke(args: argparse.Namespace) -> int:
    mix = parse_mix(args.mix)
    cfg = build_config(args, mix)
    rng = random.Random(args.seed)
    print(f"smoke test → {cfg.target}\n")
    worst = 0
    for name in mix:
        scen = SCENARIOS[name]
        client = make_client(cfg, max_conns=1)
        try:
            sample = await execute(client, scen, cfg, rng, 0.0)
        finally:
            await client.aclose()
        flag = "ok " if sample.outcome == OK else "!! "
        worst = max(worst, 0 if sample.outcome == OK else 1)
        extra = f" ttft={ms(sample.ttft)}ms deltas={sample.deltas}" if scen.sse else ""
        print(f"  {flag}{name:<14} {scen.method:<5}{scen.path:<22} "
              f"status={sample.status or '-':<5} {sample.outcome:<18} "
              f"total={ms(sample.total)}ms ttfb={ms(sample.ttfb)}ms{extra} {sample.detail}")
    return worst


def main(argv: list[str] | None = None) -> int:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--target", required=True,
                        help="edge base URL, e.g. https://aura.dau.ac.in")
    common.add_argument("--insecure", action="store_true",
                        help="skip TLS verification (self-signed staging certs)")
    common.add_argument("--http2", action="store_true",
                        help="use HTTP/2 (note: nginx limit_conn counts CONNECTIONS, "
                             "so one h2 client ≈ one connection no matter the stream count)")
    common.add_argument("--host-header", help="override the Host header (vhost/SNI testing)")
    common.add_argument("--connect-timeout", type=float, default=5.0)
    common.add_argument("--read-timeout", type=float, default=185.0,
                        help="must exceed nginx proxy_read_timeout (180s) to see real timeouts")
    common.add_argument("--user-agent", default="aura-loadtest/1.0")
    common.add_argument("--seed", type=int, default=1337)
    common.add_argument("--json", help="write the machine-readable report here")

    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_load = sub.add_parser("load", parents=[common], help="generate load")
    p_load.add_argument("--mix", type=str, default="chat=60,page=30,health=10",
                        help="scenario weights, e.g. chat=70,page=20,session=10; "
                             f"known: {', '.join(SCENARIOS)}")
    p_load.add_argument("--vus", type=int, default=50,
                        help="closed-loop virtual users, one connection each "
                             "(1000 models the spike nginx.conf is sized for)")
    p_load.add_argument("--requests", type=int,
                        help="stop after this many requests (e.g. 1000), whichever "
                             "comes first with --duration")
    p_load.add_argument("--rate", type=float,
                        help="open-loop arrival rate (req/s); overrides --vus. Use this to "
                             "observe shedding — a closed loop self-throttles and hides it")
    p_load.add_argument("--poisson", action="store_true",
                        help="Poisson (bursty) arrivals instead of evenly spaced")
    p_load.add_argument("--max-inflight", type=int, default=2000,
                        help="harness safety cap on concurrent open-loop requests")
    p_load.add_argument("--conn-pool", type=int,
                        help="open-loop client count (default min(max-inflight, 256))")
    p_load.add_argument("--duration", type=float,
                        help="seconds (default 60, or until --requests is spent)")
    p_load.add_argument("--ramp", type=float, default=10.0)
    p_load.add_argument("--spike-at", type=float, help="seconds into the run to start a spike")
    p_load.add_argument("--spike-factor", type=float, default=4.0)
    p_load.add_argument("--spike-duration", type=float, default=15.0)
    p_load.add_argument("--think-time", type=float, default=0.0,
                        help="closed-loop mean pause between a VU's requests")
    p_load.add_argument("--history-turns", type=int, default=0,
                        help="conversation turns to attach (fattens the chat body)")
    p_load.add_argument("--questions", help="file of questions, one per line")
    p_load.add_argument("--sticky-cookies", action="store_true",
                        help="keep guest cookies per VU — exercises the 10/day quota path")
    p_load.add_argument("--jwt-secret", help="INTERNAL_JWT_SECRET, for /backend/* scenarios")
    p_load.add_argument("--jwt-role", default="student",
                        choices=("student", "faculty", "admin", "guest"))
    p_load.add_argument("--jwt-erp-id", help="erpId claim (default: random per run)")
    p_load.add_argument("--bucket", type=float, default=5.0, help="timeline bucket seconds")
    p_load.add_argument("--progress-interval", type=float, default=2.0)
    p_load.add_argument("--csv", help="write per-request samples here")
    p_load.add_argument("--slo-p95-ms", type=float)
    p_load.add_argument("--slo-ttft-p95-ms", type=float)
    p_load.add_argument("--slo-error-rate", type=float, help="e.g. 0.01 for 1%%")
    p_load.add_argument("--slo-shed-rate", type=float)
    p_load.set_defaults(func=cmd_load)

    p_probe = sub.add_parser("probe", parents=[common],
                             help="assert the edge's documented semantics")
    p_probe.add_argument("--probe-burst", type=int, default=150,
                         help="concurrent requests used to trip limit_req")
    p_probe.add_argument("--slowloris-budget", type=float, default=25.0,
                         help="seconds to wait for the edge to drop a stalled header write")
    p_probe.set_defaults(func=cmd_probe)

    p_smoke = sub.add_parser("smoke", parents=[common], help="one request per scenario")
    p_smoke.add_argument("--mix", type=str, default="page=1,static=1,health=1,session=1,chat=1")
    p_smoke.add_argument("--questions")
    p_smoke.add_argument("--jwt-secret")
    p_smoke.add_argument("--jwt-role", default="student",
                         choices=("student", "faculty", "admin", "guest"))
    p_smoke.add_argument("--jwt-erp-id")
    p_smoke.set_defaults(func=cmd_smoke)

    args = parser.parse_args(argv)
    try:
        return asyncio.run(args.func(args))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
