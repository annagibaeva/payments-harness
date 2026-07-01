from harness import gates
from harness.schema import load_taskset
from harness.types import RunScore, RegressionResult


def _perfect_scores(taskset):
    out = []
    for t in taskset.tasks:
        for r in range(5):
            out.append(RunScore(task_id=t.id, run=r, correct=True, hallucinated=False,
                                detector_fired=None, latency_ms=800, cost_usd=0.0005))
    return out


def test_all_green_verdict_pass():
    ts = load_taskset()
    m = gates.compute_metrics(_perfect_scores(ts), ts, "cfg")
    g = gates.evaluate_gates(m)
    assert m.accuracy == 1.0 and m.hallucination_count == 0
    assert gates.verdict(g, None) == "PASS"


def test_one_hallucination_fails_hard_gate():
    ts = load_taskset()
    scores = _perfect_scores(ts)
    scores[0] = scores[0].model_copy(update={"correct": False, "hallucinated": True,
                                             "detector_fired": "no_canary_leak"})
    m = gates.compute_metrics(scores, ts, "cfg")
    g = gates.evaluate_gates(m)
    assert m.hallucination_count == 1
    assert gates.verdict(g, None) == "FAIL"


def test_latency_is_warn_not_blocking():
    ts = load_taskset()
    scores = [s.model_copy(update={"latency_ms": 9999}) for s in _perfect_scores(ts)]
    m = gates.compute_metrics(scores, ts, "cfg")
    g = gates.evaluate_gates(m)
    lat = next(x for x in g if x.name == "latency_p95")
    assert lat.passed is False and lat.blocking is False
    assert gates.verdict(g, None) == "PASS"   # warn doesn't block


def test_regression_fail_blocks_verdict():
    ts = load_taskset()
    m = gates.compute_metrics(_perfect_scores(ts), ts, "cfg")
    g = gates.evaluate_gates(m)
    reg = RegressionResult(compared=True, passed=False, regressions=["accuracy dropped"])
    assert gates.verdict(g, reg) == "FAIL"
