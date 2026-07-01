from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from . import config
from .types import (FailureCard, GateResult, Metrics, RegressionResult,
                    Report, RunScore, TaskSet)

_TEMPLATES = config.ROOT / "templates"


def build_failure_cards(run_scores: list[RunScore], taskset: TaskSet) -> list[FailureCard]:
    tasks = {t.id: t for t in taskset.tasks}
    by_task: dict[str, list[RunScore]] = defaultdict(list)
    for s in run_scores:
        by_task[s.task_id].append(s)
    cards: list[FailureCard] = []
    for tid, scores in by_task.items():
        bad = [s for s in scores if not s.correct]
        if not bad:
            continue
        t = tasks[tid]
        worst = next((s for s in bad if s.hallucinated), bad[0])
        gate = "hallucination" if worst.hallucinated else "accuracy"
        cards.append(FailureCard(
            task_id=tid, intent=t.intent, prompt=t.prompt,
            expected=t.expected.model_dump_json(),
            actual="(no response)", gate_breached=gate,
            why=(f"detector {worst.detector_fired} fired" if worst.hallucinated
                 else f"{len(bad)}/{len(scores)} runs failed the answer match"),
        ))
    return cards


def build_report(verdict: str, gates: list[GateResult], metrics: Metrics,
                 regression: RegressionResult | None, failures: list[FailureCard]) -> Report:
    return Report(verdict=verdict, gates=gates, metrics=metrics,
                  regression=regression, failures=failures)


def write_report(report: Report, json_path: Path = config.REPORT_JSON_PATH,
                 html_path: Path = config.DASHBOARD_PATH) -> None:
    Path(json_path).parent.mkdir(parents=True, exist_ok=True)
    Path(json_path).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    env = Environment(loader=FileSystemLoader(str(_TEMPLATES)), autoescape=True)
    html = env.get_template("dashboard.html.j2").render(report=report)
    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    Path(html_path).write_text(html, encoding="utf-8")
