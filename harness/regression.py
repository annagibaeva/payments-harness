from __future__ import annotations

import json
from pathlib import Path

from . import config
from .types import Baseline, Metrics, RegressionResult


def load_baseline(path: Path = config.BASELINE_PATH) -> Baseline | None:
    if not Path(path).exists():
        return None
    return Baseline.model_validate(json.loads(Path(path).read_text(encoding="utf-8")))


def compare(m: Metrics, baseline: Baseline | None) -> RegressionResult:
    if baseline is None:
        return RegressionResult(compared=False, passed=True, reason="no baseline (first run)")
    b = baseline.metrics
    if (b.benchmark_version, b.fixtures_version, b.config_hash) != \
       (m.benchmark_version, m.fixtures_version, m.config_hash):
        return RegressionResult(compared=False, passed=True,
                                reason="version/config mismatch — re-pin baseline")
    R = config.RegressionTolerance
    regs: list[str] = []
    if m.accuracy < b.accuracy - R.ACCURACY_DROP_PP:
        regs.append(f"accuracy {b.accuracy:.3f}->{m.accuracy:.3f}")
    if m.passk_general < b.passk_general - R.PASSK_GENERAL_DROP_PP:
        regs.append(f"passk_general {b.passk_general:.3f}->{m.passk_general:.3f}")
    if m.passk_safety < b.passk_safety - R.PASSK_SAFETY_DROP_PP:
        regs.append(f"passk_safety {b.passk_safety:.3f}->{m.passk_safety:.3f}")
    if m.hallucination_count > b.hallucination_count:
        regs.append(f"hallucination {b.hallucination_count}->{m.hallucination_count}")
    if m.cost_usd_total > b.cost_usd_total * (1 + R.COST_INCREASE_PCT):
        regs.append(f"cost {b.cost_usd_total:.4f}->{m.cost_usd_total:.4f}")
    if m.latency_p95_ms > b.latency_p95_ms * (1 + R.LATENCY_INCREASE_PCT):
        regs.append(f"latency_p95 {b.latency_p95_ms:.0f}->{m.latency_p95_ms:.0f}")
    return RegressionResult(compared=True, passed=not regs, regressions=regs)
