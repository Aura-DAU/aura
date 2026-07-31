# metrics_multiproc.py — prometheus_client multiprocess-mode plumbing (OBS-01).
#
# The backend serves under gunicorn with N uvicorn workers (server/Dockerfile
# CMD, WEB_CONCURRENCY/BACKEND_WORKERS). Each worker holds its own in-process
# registry, so a /metrics scrape returns whichever worker happened to answer
# it: consecutive scrapes alternate between per-worker values and every counter
# looks non-monotonic and under-counted. prometheus_client's multiprocess mode
# fixes this by having each worker write its samples into mmapped .db files in
# a shared directory, which the scrape endpoint aggregates into one view.
#
# Two constraints shape this module:
#
#   1. `prometheus_client.values.ValueClass` is bound once, at import time,
#      from PROMETHEUS_MULTIPROC_DIR. The directory therefore has to be
#      validated *before* prometheus_client is imported — if it is missing or
#      unwritable, the first metric construction raises and the process dies at
#      import. `bootstrap()` runs that validation and clears the variable when
#      the path is unusable, so a broken metrics config degrades to the old
#      single-registry behaviour instead of taking down the API.
#
#   2. The directory may only be wiped by the master process *before* it forks
#      workers. Wiping it from inside a worker would delete its siblings' live
#      files. `reset_dir()` is called from gunicorn's `on_starting` hook
#      (server/gunicorn.conf.py) and must never be called from request or
#      startup code paths.
#
# Nothing here imports prometheus_client at module scope — that import must not
# happen until bootstrap() has settled the environment.

import glob
import os
import sys
import tempfile

# prometheus_client honours both spellings; the lowercase one is its legacy
# name. Both have to be handled or a stale lowercase value silently wins.
_ENV_VARS = ("PROMETHEUS_MULTIPROC_DIR", "prometheus_multiproc_dir")

_state: dict[str, object] = {"dir": None, "reason": "not initialised"}


def _log(message: str) -> None:
    print(f"[metrics] {message}", flush=True)


def configured_dir() -> str | None:
    """The multiprocess directory requested via the environment, if any."""
    for name in _ENV_VARS:
        raw = (os.environ.get(name) or "").strip()
        if raw:
            return raw
    return None


def _prepare(path: str) -> bool:
    """Create `path` and confirm this process can write into it."""
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, f".writable-{os.getpid()}")
        with open(probe, "wb"):
            pass
        os.remove(probe)
        return True
    except OSError as exc:
        _log(f"multiprocess dir {path!r} unusable: {exc}")
        return False


def _set_env(path: str) -> None:
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = path
    os.environ.pop("prometheus_multiproc_dir", None)


def _clear_env() -> None:
    for name in _ENV_VARS:
        os.environ.pop(name, None)


def _already_bound_to_multiproc() -> bool:
    """True when prometheus_client.values has already picked the multiprocess
    ValueClass. Once that has happened the env var can no longer be cleared —
    metric construction would fail on a `None` directory — so the only safe
    degradation left is to point it somewhere writable."""
    values = sys.modules.get("prometheus_client.values")
    if values is None:
        return False
    # MutexValue for single-process, MmapedValue (built by MultiProcessValue)
    # for multiprocess mode.
    return getattr(values.ValueClass, "__name__", "") == "MmapedValue"


def bootstrap() -> str | None:
    """Settle multiprocess mode before prometheus_client is imported.

    Returns the directory being used, or None when metrics fall back to a
    single in-process registry. Never raises.
    """
    try:
        path = configured_dir()
        if not path:
            _state.update(dir=None, reason="PROMETHEUS_MULTIPROC_DIR unset")
            return None

        if _prepare(path):
            _set_env(path)
            _state.update(dir=path, reason="enabled")
            return path

        if _already_bound_to_multiproc():
            # prometheus_client is already committed to multiprocess mode, so
            # clearing the variable would crash the first metric. Give it a
            # writable path instead and be loud: metrics are per-process again
            # (the OBS-01 symptom) but the API stays up.
            fallback = tempfile.mkdtemp(prefix="aura-prom-multiproc-")
            if _prepare(fallback):
                _set_env(fallback)
                _state.update(dir=fallback, reason="degraded-tempdir")
                _log(
                    f"falling back to per-process {fallback!r} — scrapes will "
                    "NOT aggregate across workers"
                )
                return fallback

        _clear_env()
        _state.update(dir=None, reason="disabled-unusable-dir")
        _log("multiprocess mode disabled; /metrics reports this worker only")
        return None
    except Exception as exc:  # pragma: no cover — metrics must never crash boot
        _clear_env()
        _state.update(dir=None, reason=f"disabled-{type(exc).__name__}")
        _log(f"multiprocess bootstrap failed ({exc}); metrics stay per-process")
        return None


def active_dir() -> str | None:
    return _state["dir"]  # type: ignore[return-value]


def status() -> str:
    path = active_dir()
    if path:
        return f"multiprocess mode {_state['reason']} at {path}"
    return f"single-registry mode ({_state['reason']})"


def reset_dir() -> int:
    """Delete every sample file in the multiprocess directory.

    Call ONLY from the master process before it forks workers (gunicorn
    `on_starting`). Stale files left by dead workers are indistinguishable from
    live ones to the aggregator, so without this a counter keeps the readings of
    every worker that has ever run and never returns to zero after a restart.
    Returns the number of files removed.
    """
    path = configured_dir()
    if not path:
        return 0
    removed = 0
    try:
        for filename in glob.glob(os.path.join(path, "*.db")):
            try:
                os.remove(filename)
                removed += 1
            except OSError as exc:
                _log(f"could not remove stale {filename}: {exc}")
    except Exception as exc:  # pragma: no cover
        _log(f"reset_dir failed: {exc}")
    if removed:
        _log(f"cleared {removed} stale sample file(s) from {path}")
    return removed


def mark_process_dead(pid: int) -> None:
    """Drop a dead worker's live-gauge files (gunicorn `child_exit`).

    Only `gauge_live*` files are removed — counters and histograms from a
    recycled worker must survive, or the aggregated totals would fall when
    gunicorn hits --max-requests and the series would stop being monotonic.
    """
    path = configured_dir()
    if not path:
        return
    try:
        from prometheus_client import multiprocess  # noqa: PLC0415 — post-bootstrap

        multiprocess.mark_process_dead(pid, path)
    except Exception as exc:  # pragma: no cover
        _log(f"mark_process_dead({pid}) failed: {exc}")


def build_registry():
    """A registry whose only collector aggregates every worker's sample files.

    The default registry is deliberately not reused: in multiprocess mode it
    holds this worker's values plus the per-process `process_*`/`python_info`
    collectors, which cannot be aggregated and are not exported here.
    """
    from prometheus_client import CollectorRegistry, multiprocess  # noqa: PLC0415

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry, path=active_dir())
    return registry


def main(argv: list[str] | None = None) -> int:
    """`python -m api.metrics_multiproc --reset` — clear the directory before
    starting a multi-worker server by hand (uvicorn --workers has no pre-fork
    hook; gunicorn deployments get this from server/gunicorn.conf.py)."""
    args = sys.argv[1:] if argv is None else argv
    if "--reset" in args:
        path = configured_dir()
        if not path:
            _log("PROMETHEUS_MULTIPROC_DIR unset — nothing to reset")
            return 0
        _prepare(path)
        reset_dir()
        return 0
    print(__doc__ or main.__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
