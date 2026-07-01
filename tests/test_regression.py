from harness import regression
from harness.types import Metrics, Baseline


def _m(**kw):
    base = dict(accuracy=1.0, hallucination_count=0, passk_general=1.0, passk_safety=1.0,
                cost_usd_total=0.02, latency_p95_ms=800, benchmark_version="benchmark-v1",
                fixtures_version="fixtures-v1", config_hash="cfg")
    base.update(kw)
    return Metrics(**base)


def test_no_baseline_is_noop_pass():
    r = regression.compare(_m(), None)
    assert r.compared is False and r.passed is True


def test_version_mismatch_is_noop():
    b = Baseline(metrics=_m(config_hash="OLD"))
    r = regression.compare(_m(config_hash="NEW"), b)
    assert r.compared is False and r.passed is True and "mismatch" in r.reason


def test_accuracy_drop_flags_regression():
    b = Baseline(metrics=_m(accuracy=1.0))
    r = regression.compare(_m(accuracy=0.93), b)
    assert r.compared is True and r.passed is False and r.regressions


def test_within_tolerance_passes():
    b = Baseline(metrics=_m(cost_usd_total=0.02, latency_p95_ms=800))
    r = regression.compare(_m(cost_usd_total=0.022, latency_p95_ms=900), b)  # +10% cost, +12% lat
    assert r.passed is True
