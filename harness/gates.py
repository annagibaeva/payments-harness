from __future__ import annotations

from collections import defaultdict

from .config import Thresholds
from .types import GateResult, Metrics, RegressionResult, RunScore, TaskSet


def compute_metrics(run_scores: list[RunScore], taskset: TaskSet, config_hash: str) -> Metrics:
    total = len(run_scores)
    accuracy = sum(s.correct for s in run_scores) / total if total else 0.0
    hallucination_count = sum(s.hallucinated for s in run_scores)

    by_task: dict[str, list[RunScore]] = defaultdict(list)
    for s in run_scores:
        by_task[s.task_id].append(s)
    layer = {t.id: t.layer for t in taskset.tasks}

    def passk(tid: str) -> bool:
        return all(s.correct for s in by_task[tid])

    gen = [t for t in by_task if layer.get(t) == "plumbing"]
    saf = [t for t in by_task if layer.get(t) == "safety"]
    passk_general = sum(passk(t) for t in gen) / len(gen) if gen else 1.0
    passk_safety = sum(passk(t) for t in saf) / len(saf) if saf else 1.0

    lat = sorted(s.latency_ms for s in run_scores)
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)))] if lat else 0.0

    return Metrics(
        accuracy=accuracy, hallucination_count=hallucination_count,
        passk_general=passk_general, passk_safety=passk_safety,
        cost_usd_total=sum(s.cost_usd for s in run_scores), latency_p95_ms=p95,
        benchmark_version=taskset.version, fixtures_version=taskset.fixtures,
        config_hash=config_hash,
    )


def evaluate_gates(m: Metrics) -> list[GateResult]:
    T = Thresholds
    return [
        GateResult(name="accuracy", passed=m.accuracy >= T.ACCURACY_MIN, blocking=True,
                   observed=round(m.accuracy, 3), threshold=T.ACCURACY_MIN, detail="mean correct-rate"),
        GateResult(name="hallucination", passed=m.hallucination_count <= T.HALLUCINATION_MAX,
                   blocking=True, observed=m.hallucination_count, threshold=T.HALLUCINATION_MAX,
                   detail="zero-tolerance"),
        GateResult(name="passk_general", passed=m.passk_general >= T.PASSK_GENERAL_MIN, blocking=True,
                   observed=round(m.passk_general, 3), threshold=T.PASSK_GENERAL_MIN, detail="plumbing pass^k"),
        GateResult(name="passk_safety", passed=m.passk_safety >= T.PASSK_SAFETY_MIN, blocking=True,
                   observed=round(m.passk_safety, 3), threshold=T.PASSK_SAFETY_MIN, detail="safety pass^k"),
        GateResult(name="cost", passed=m.cost_usd_total <= T.COST_MAX_USD, blocking=True,
                   observed=round(m.cost_usd_total, 4), threshold=T.COST_MAX_USD, detail="computed from usage"),
        GateResult(name="latency_p95", passed=m.latency_p95_ms <= T.LATENCY_P95_MS, blocking=False,
                   observed=round(m.latency_p95_ms, 1), threshold=T.LATENCY_P95_MS, detail="WARN only in v1"),
    ]


def verdict(gates: list[GateResult], regression: RegressionResult | None) -> str:
    blocking_ok = all(g.passed for g in gates if g.blocking)
    reg_ok = regression is None or regression.passed
    return "PASS" if (blocking_ok and reg_ok) else "FAIL"
