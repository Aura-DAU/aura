# gunicorn.conf.py — Prometheus multiprocess directory lifecycle (OBS-01).
#
# Gunicorn auto-loads `gunicorn.conf.py` from its working directory when no -c
# is passed, and the image's WORKDIR is /app/server (server/Dockerfile), so
# this file is picked up by the existing CMD with no change to it. It sets no
# server options — workers, bind and timeouts stay where they are, on the
# command line — and defines only the two hooks that need to run in the master
# process:
#
#   on_starting  (master, before any worker exists) — wipe the sample
#       directory. Files left by workers from a previous boot are
#       indistinguishable from live ones to the aggregator, so without this the
#       totals include every process that has ever run and never reset.
#
#   child_exit   (master, on worker death) — drop that worker's live-gauge
#       files. Counter and histogram files are intentionally kept: gunicorn
#       recycles workers at --max-requests, and deleting their samples would
#       make the aggregated counters fall.
#
# Both hooks are best-effort. A metrics bookkeeping failure must never stop the
# master from starting or reaping workers.

import os
import sys

_server_dir = os.path.dirname(os.path.abspath(__file__))
if _server_dir not in sys.path:
    sys.path.insert(0, _server_dir)


def on_starting(server):
    try:
        from api import metrics_multiproc

        path = metrics_multiproc.configured_dir()
        if not path:
            server.log.info("[metrics] PROMETHEUS_MULTIPROC_DIR unset — "
                            "per-worker registries (see OBS-01)")
            return
        metrics_multiproc.bootstrap()
        removed = metrics_multiproc.reset_dir()
        server.log.info(
            "[metrics] multiprocess dir %s ready (%d stale file(s) removed)",
            path, removed,
        )
    except Exception as exc:
        server.log.warning("[metrics] multiproc dir setup skipped: %s", exc)


def child_exit(server, worker):
    try:
        from api import metrics_multiproc

        metrics_multiproc.mark_process_dead(worker.pid)
    except Exception as exc:
        server.log.warning("[metrics] mark_process_dead(%s) failed: %s",
                           worker.pid, exc)
