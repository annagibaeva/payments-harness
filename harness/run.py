# harness/run.py  (replace the file body)
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import cassette, config, detectors, gates, regression, report, scorer, schema
from .types import Response


def _cassette_file() -> Path:
    return config.RESPONSES_DIR / "golden.jsonl"


def run(record: bool = False) -> int:
    taskset, fixtures = schema.validate_all()
    cfg = config.config_hash(taskset.version, fixtures.version)
    cpath = _cassette_file()
    cache = cassette.load(cpath, cfg)

    client = None
    if record:
        import anthropic
        client = anthropic.Anthropic()
        from agent import assistant

    run_scores = []
    for task in taskset.tasks:
        for r in range(config.K):
            hit = cache.get(cassette.key(task.id, r, cfg))
            if hit is not None:
                resp = hit
            elif record:
                text, lat, cost = assistant.generate(task.prompt, fixtures, client)
                resp = Response(task_id=task.id, run=r, text=text, latency_ms=lat,
                                cost_usd=cost, from_cassette=False)
                cassette.append(cpath, resp, cfg)
            else:
                print(f"MISSING cassette entry for {task.id} run {r}; run with --record",
                      file=sys.stderr)
                return 1
            fired = detectors.run_detectors(task, resp.text, fixtures)
            run_scores.append(scorer.score_run(task, resp.text, fired, r,
                                               resp.latency_ms, resp.cost_usd, resp.from_cassette))

    metrics = gates.compute_metrics(run_scores, taskset, cfg)
    gate_results = gates.evaluate_gates(metrics)
    reg = regression.compare(metrics, regression.load_baseline())
    v = gates.verdict(gate_results, reg)
    cards = report.build_failure_cards(run_scores, taskset)
    rep = report.build_report(v, gate_results, metrics, reg, cards)
    report.write_report(rep, config.REPORT_JSON_PATH, config.DASHBOARD_PATH)   # flush BEFORE exiting
    print(f"{v}  accuracy={metrics.accuracy:.3f}  halluc={metrics.hallucination_count}  "
          f"passk_safety={metrics.passk_safety:.2f}  cost=${metrics.cost_usd_total:.4f}")
    return 0 if v == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--record", action="store_true", help="call the model for missing entries")
    args = ap.parse_args(argv)
    return run(record=args.record)


if __name__ == "__main__":
    raise SystemExit(main())
