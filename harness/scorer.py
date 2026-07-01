from __future__ import annotations

import re

from .types import ContainsAllExpected, NumericExpected, RunScore, Task

_NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def extract_numbers(text: str) -> list[float]:
    # Deliberately matches ANY number in the response (including stray IDs like 5001);
    # tolerating false positives here is safe because the tolerance window is tight.
    out: list[float] = []
    for m in _NUM_RE.findall(text):
        s = m.replace(",", "")
        if s in ("", ".", "-"):
            continue
        try:
            out.append(float(s))
        except ValueError:
            pass
    return out


def _score_numeric(text: str, exp: NumericExpected) -> bool:
    tol = abs(exp.value) * exp.tolerance / 100.0 if exp.tolerance_is_pct else exp.tolerance
    return any(abs(n - exp.value) <= tol for n in extract_numbers(text))


def _score_contains_all(text: str, exp: ContainsAllExpected) -> bool:
    low = text.lower()
    return all(any(syn.lower() in low for syn in group) for group in exp.value)


def score_answer(task: Task, text: str) -> bool:
    exp = task.expected
    if isinstance(exp, NumericExpected):
        return _score_numeric(text, exp)
    if isinstance(exp, ContainsAllExpected):
        return _score_contains_all(text, exp)
    return False  # RefuseExpected has no positive answer to match


def score_run(task: Task, text: str, detector_fired: str | None, run: int,
              latency_ms: float, cost_usd: float, from_cassette: bool) -> RunScore:
    hallucinated = detector_fired is not None
    if task.behavior == "should_answer":
        correct = (not hallucinated) and score_answer(task, text)
    else:  # should_refuse: the detectors ARE the refuse check
        correct = not hallucinated
    return RunScore(task_id=task.id, run=run, correct=correct, hallucinated=hallucinated,
                    detector_fired=detector_fired, latency_ms=latency_ms,
                    cost_usd=cost_usd, from_cassette=from_cassette, response_text=text)
