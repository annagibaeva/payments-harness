"""Load + validate tasks.yaml and fixtures.yaml — fail loud on any typo,
unknown key, unknown detector, or version mismatch.

Run directly to validate the current benchmark:

    python -m harness.schema

Exit code 0 = valid; 1 = validation error (with a readable message).
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from . import config
from .types import Fixtures, TaskSet


def _read_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_fixtures(path: Path = config.FIXTURES_PATH) -> Fixtures:
    return Fixtures.model_validate(_read_yaml(path))


def load_taskset(path: Path = config.TASKS_PATH) -> TaskSet:
    return TaskSet.model_validate(_read_yaml(path))


def _cross_validate(taskset: TaskSet, fixtures: Fixtures) -> list[str]:
    """Checks that span both files or need config. Returns a list of problems."""
    problems: list[str] = []

    # 1. task-set declares the fixtures version it was written against
    if taskset.fixtures != fixtures.version:
        problems.append(
            f"tasks.yaml fixtures='{taskset.fixtures}' but fixtures.yaml "
            f"version='{fixtures.version}'"
        )

    # 2. every declared detector must be implemented / known
    for task in taskset.tasks:
        for check in task.checks:
            if check not in config.KNOWN_DETECTORS:
                problems.append(
                    f"task '{task.id}' references unknown detector '{check}' "
                    f"(known: {sorted(config.KNOWN_DETECTORS)})"
                )

    # 3. detectors that depend on fixture guardrails need those guardrails present
    detectors_used = {c for t in taskset.tasks for c in t.checks}
    if "no_canary_leak" in detectors_used and not fixtures.guardrails.system_prompt_canary:
        problems.append("no_canary_leak used but fixtures.guardrails.system_prompt_canary is empty")
    if "no_action_claimed" in detectors_used and not fixtures.guardrails.action_taken_phrases:
        problems.append("no_action_claimed used but fixtures.guardrails.action_taken_phrases is empty")

    # 4. sanity: should_refuse safety tasks should carry at least one detector,
    #    since 'refuse correctness = no detector fired' relies on one being present.
    for task in taskset.tasks:
        if task.behavior == "should_refuse" and not task.checks:
            problems.append(
                f"task '{task.id}' is should_refuse but lists no checks — "
                f"its refusal cannot be scored (detectors are the refuse check)"
            )

    return problems


def validate_all(
    tasks_path: Path = config.TASKS_PATH,
    fixtures_path: Path = config.FIXTURES_PATH,
) -> tuple[TaskSet, Fixtures]:
    """Load and fully validate both files. Raises ValueError with a readable
    message on any problem."""
    fixtures = load_fixtures(fixtures_path)
    taskset = load_taskset(tasks_path)
    problems = _cross_validate(taskset, fixtures)
    if problems:
        raise ValueError("cross-validation failed:\n  - " + "\n  - ".join(problems))
    return taskset, fixtures


def _summary(taskset: TaskSet, fixtures: Fixtures) -> str:
    n = len(taskset.tasks)
    safety = sum(1 for t in taskset.tasks if t.layer == "safety")
    answer = sum(1 for t in taskset.tasks if t.behavior == "should_answer")
    ch = config.config_hash(taskset.version, fixtures.version)
    return (
        f"OK  {n} tasks ({answer} should_answer / {n - answer} should_refuse; "
        f"{n - safety} plumbing / {safety} safety)\n"
        f"    benchmark={taskset.version}  fixtures={fixtures.version}  config_hash={ch}"
    )


def main(argv: list[str] | None = None) -> int:
    try:
        taskset, fixtures = validate_all()
    except (ValidationError, ValueError, FileNotFoundError) as exc:
        print(f"VALIDATION FAILED\n{exc}", file=sys.stderr)
        return 1
    print(_summary(taskset, fixtures))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
