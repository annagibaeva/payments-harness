"""Phase 0 exit-criterion tests: the real benchmark validates, and a bad task
key / unknown detector fails loudly."""
from __future__ import annotations

import copy

import pytest
import yaml
from pydantic import ValidationError

from harness import config, schema
from harness.types import TaskSet


def test_real_benchmark_validates():
    taskset, fixtures = schema.validate_all()
    assert len(taskset.tasks) == 19
    assert taskset.fixtures == fixtures.version
    # composition guard: 10 safety, 10 should_answer (anti-gaming balance).
    # payment-03 is should_answer (answer "pending" while resisting injection).
    assert sum(t.layer == "safety" for t in taskset.tasks) == 10
    assert sum(t.behavior == "should_answer" for t in taskset.tasks) == 10
    assert sum(t.behavior == "should_refuse" for t in taskset.tasks) == 9


def _raw_tasks() -> dict:
    with open(config.TASKS_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_unknown_key_fails_loudly():
    raw = _raw_tasks()
    raw["tasks"][0]["expexted"] = {"type": "numeric", "value": 1.0}  # typo'd key
    with pytest.raises(ValidationError):
        TaskSet.model_validate(raw)


def test_duplicate_id_fails():
    raw = _raw_tasks()
    raw["tasks"][1]["id"] = raw["tasks"][0]["id"]
    with pytest.raises(ValidationError):
        TaskSet.model_validate(raw)


def test_unknown_detector_fails_cross_validation():
    raw = _raw_tasks()
    raw["tasks"][0]["checks"] = ["no_such_detector"]
    taskset = TaskSet.model_validate(raw)
    fixtures = schema.load_fixtures()
    problems = schema._cross_validate(taskset, fixtures)
    assert any("unknown detector" in p for p in problems)


def test_fixtures_version_mismatch_fails():
    taskset = schema.load_taskset()
    fixtures = schema.load_fixtures()
    bad = copy.deepcopy(fixtures)
    bad.version = "fixtures-vX"
    problems = schema._cross_validate(taskset, bad)
    assert any("fixtures" in p for p in problems)


def test_config_hash_changes_with_version():
    a = config.config_hash("benchmark-v1", "fixtures-v1")
    b = config.config_hash("benchmark-v2", "fixtures-v1")
    assert a != b and len(a) == 12
