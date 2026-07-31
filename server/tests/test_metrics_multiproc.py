# Guards the OBS-01 fix: /metrics must aggregate across uvicorn workers, must
# fall back to a single registry when the shared directory is unusable, and must
# not grow a Gauge without an explicit multiprocess_mode.

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parent.parent
for _p in (str(_SERVER_DIR), str(_SERVER_DIR / "rag")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from api import metrics_multiproc  # noqa: E402

_ENV_VARS = ("PROMETHEUS_MULTIPROC_DIR", "prometheus_multiproc_dir")

# Runs in a fresh interpreter so it gets its own prometheus_client import (and
# therefore its own mmapped sample files), the way a forked worker does.
_WRITER = """
import sys
sys.path.insert(0, {server!r})
from api.metrics import INFERENCE_NODE_REQUESTS, MULTIPROC_DIR
assert MULTIPROC_DIR, "multiprocess mode did not engage in the writer"
for _ in range({n}):
    INFERENCE_NODE_REQUESTS.labels(node="10.100.97.71:8001").inc()
"""


class EnvSandbox(unittest.TestCase):
    def setUp(self):
        self._saved = {name: os.environ.get(name) for name in _ENV_VARS}
        for name in _ENV_VARS:
            os.environ.pop(name, None)

    def tearDown(self):
        for name, value in self._saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class TestBootstrapFallback(EnvSandbox):
    def test_unset_env_falls_back_to_single_registry(self):
        self.assertIsNone(metrics_multiproc.bootstrap())
        self.assertIn("single-registry", metrics_multiproc.status())

    def test_unwritable_dir_disables_instead_of_raising(self):
        # A path under a regular file can never be created.
        with tempfile.NamedTemporaryFile() as blocker:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = os.path.join(blocker.name, "sub")
            self.assertIsNone(metrics_multiproc.bootstrap())
        self.assertIsNone(os.environ.get("PROMETHEUS_MULTIPROC_DIR"))

    def test_writable_dir_enables_and_is_created(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "created-on-demand")
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = target
            self.assertEqual(metrics_multiproc.bootstrap(), target)
            self.assertTrue(os.path.isdir(target))
            self.assertEqual(metrics_multiproc.active_dir(), target)

    def test_legacy_lowercase_env_var_is_honoured(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["prometheus_multiproc_dir"] = tmp
            self.assertEqual(metrics_multiproc.bootstrap(), tmp)
            self.assertEqual(os.environ["PROMETHEUS_MULTIPROC_DIR"], tmp)


class TestResetDir(EnvSandbox):
    def test_reset_removes_only_sample_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = tmp
            Path(tmp, "counter_1234.db").write_bytes(b"")
            Path(tmp, "gauge_livesum_1234.db").write_bytes(b"")
            Path(tmp, "README").write_text("keep me")
            self.assertEqual(metrics_multiproc.reset_dir(), 2)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], ["README"])

    def test_reset_is_a_noop_without_the_env_var(self):
        self.assertEqual(metrics_multiproc.reset_dir(), 0)


class TestCrossProcessAggregation(EnvSandbox):
    """The actual OBS-01 regression: two processes increment the same series and
    a single scrape must report their sum, not one process's slice."""

    def _sample_value(self, registry, metric, labels):
        return registry.get_sample_value(metric, labels)

    def test_scrape_sums_every_worker(self):
        from prometheus_client import CollectorRegistry, multiprocess

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = tmp
            env = dict(os.environ, PROMETHEUS_MULTIPROC_DIR=tmp)
            for count in (16, 18):
                subprocess.run(
                    [sys.executable, "-c",
                     _WRITER.format(server=str(_SERVER_DIR), n=count)],
                    check=True, env=env, capture_output=True, text=True,
                )

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry, path=tmp)
            value = self._sample_value(
                registry,
                "aura_inference_node_requests_total",
                {"node": "10.100.97.71:8001"},
            )
            # 16 and 18 are the two alternating readings OBS-01 recorded.
            self.assertEqual(value, 34.0)

    def test_dead_worker_counters_survive_mark_process_dead(self):
        from prometheus_client import CollectorRegistry, multiprocess

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["PROMETHEUS_MULTIPROC_DIR"] = tmp
            env = dict(os.environ, PROMETHEUS_MULTIPROC_DIR=tmp)
            proc = subprocess.run(
                [sys.executable, "-c",
                 _WRITER.format(server=str(_SERVER_DIR), n=7)],
                check=True, env=env, capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 0)
            for db in Path(tmp).glob("counter_*.db"):
                pid = int(db.stem.split("_")[-1])
                metrics_multiproc.mark_process_dead(pid)

            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry, path=tmp)
            self.assertEqual(
                registry.get_sample_value(
                    "aura_inference_node_requests_total",
                    {"node": "10.100.97.71:8001"},
                ),
                7.0,
            )


class TestMetricTypeAudit(unittest.TestCase):
    """Multiprocess mode changes Gauge semantics: without an explicit
    multiprocess_mode a Gauge fans out one series per worker under a synthetic
    `pid` label. Counters and Histograms sum, which is what we want."""

    _EXPLICIT_MODES = {"min", "max", "livesum", "liveall", "mostrecent", "livemostrecent"}

    def test_no_gauge_without_an_explicit_multiprocess_mode(self):
        from prometheus_client.metrics import MetricWrapperBase

        from api import metrics

        offenders = []
        for name, obj in vars(metrics).items():
            if not isinstance(obj, MetricWrapperBase):
                continue
            if obj._type in {"counter", "histogram"}:
                continue
            mode = getattr(obj, "_multiprocess_mode", None)
            if mode not in self._EXPLICIT_MODES:
                offenders.append(f"{name} ({obj._type}, mode={mode!r})")
        self.assertEqual(
            offenders, [],
            "set an explicit multiprocess_mode on: " + ", ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
