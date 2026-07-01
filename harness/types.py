"""Contract types — the frozen interfaces every downstream module builds against.

Two families:
  1. YAML-backed, STRICT (extra keys forbidden so a typo fails loudly):
     Expected / Task / TaskSet / Fixtures.
  2. Runtime data passed between modules: Response -> RunScore -> TaskResult
     -> Metrics -> GateResult / RegressionResult -> Report.

Nothing here imports config (keeps the type layer dependency-free); cross-field
validation that needs config lives in schema.py.
"""
from __future__ import annotations

from typing import Annotated, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ===================================================================== tasks
class NumericExpected(_Strict):
    type: Literal["numeric"]
    value: float
    tolerance: float = 0.0
    tolerance_is_pct: bool = False   # if True, tolerance is a % of value


class ContainsAllExpected(_Strict):
    type: Literal["contains_all"]
    # List of synonym groups: OR within a group, AND across groups.
    value: list[list[str]]

    @model_validator(mode="after")
    def _non_empty(self) -> "ContainsAllExpected":
        if not self.value or any(not group for group in self.value):
            raise ValueError("contains_all: every synonym group must be non-empty")
        return self


class RefuseExpected(_Strict):
    type: Literal["refuse"]
    note: str = ""   # human documentation only — NOT machine-matched


Expected = Annotated[
    Union[NumericExpected, ContainsAllExpected, RefuseExpected],
    Field(discriminator="type"),
]


class Task(_Strict):
    id: str
    intent: str
    split: Literal["golden", "adversarial"]
    layer: Literal["plumbing", "safety"]
    behavior: Literal["should_answer", "should_refuse"]
    gate_profile: str                 # carried but INERT in v1 (V2 per-intent SLAs)
    prompt: str
    expected: Expected
    checks: list[str] = Field(default_factory=list)   # detector names; validated in schema.py


class TaskSet(_Strict):
    version: str                      # e.g. benchmark-v1
    fixtures: str                     # must match Fixtures.version
    tasks: list[Task]

    @model_validator(mode="after")
    def _unique_ids(self) -> "TaskSet":
        ids = [t.id for t in self.tasks]
        dupes = {i for i in ids if ids.count(i) > 1}
        if dupes:
            raise ValueError(f"duplicate task ids: {sorted(dupes)}")
        return self


# ================================================================== fixtures
class Session(_Strict):
    user: str
    authorized_account: str


class Guardrails(_Strict):
    system_prompt_canary: str
    action_taken_phrases: list[str]


class Account(_Strict):
    holder: str
    balances: dict[str, float]


class Capabilities(_Strict):
    read_only: bool


class Fixtures(_Strict):
    version: str
    session: Session
    guardrails: Guardrails
    accounts: dict[str, Account]
    fx_rates: dict[str, float]
    # These three carry heterogeneous per-record shapes; kept permissive on purpose.
    fee_schedule: dict[str, dict]
    payments: dict[str, dict]
    disputes: dict[str, dict]
    capabilities: Capabilities


# ============================================================ runtime records
class Response(BaseModel):
    """One assistant response for one task on one run (recorded to / replayed
    from the cassette)."""
    task_id: str
    run: int
    text: str
    latency_ms: float
    cost_usd: float
    from_cassette: bool = False


class RunScore(BaseModel):
    """Deterministic score of a single Response."""
    task_id: str
    run: int
    correct: bool
    hallucinated: bool
    detector_fired: Optional[str] = None
    latency_ms: float
    cost_usd: float
    from_cassette: bool = False


class TaskResult(BaseModel):
    """Aggregate of k RunScores for one task."""
    task_id: str
    layer: Literal["plumbing", "safety"]
    correct_runs: int
    total_runs: int
    passk: bool               # True iff all k runs correct
    hallucinated_any: bool


class Metrics(BaseModel):
    accuracy: float                    # mean correct-rate over all k*tasks
    hallucination_count: int           # total hallucinated runs
    passk_general: float               # fraction of plumbing tasks that pass^k
    passk_safety: float                # fraction of safety tasks that pass^k
    cost_usd_total: float
    latency_p95_ms: float
    benchmark_version: str
    fixtures_version: str
    config_hash: str


class GateResult(BaseModel):
    name: str
    passed: bool
    blocking: bool                     # latency is non-blocking (warn) in v1
    observed: Union[float, int, str]
    threshold: Union[float, int, str]
    detail: str = ""


class RegressionResult(BaseModel):
    compared: bool                     # False = no-op (no baseline or version mismatch)
    passed: bool = True
    reason: str = ""                   # why it no-op'd, if it did
    regressions: list[str] = Field(default_factory=list)


class FailureCard(BaseModel):
    task_id: str
    intent: str
    prompt: str
    expected: str
    actual: str
    gate_breached: str
    why: str


class Report(BaseModel):
    verdict: Literal["PASS", "FAIL"]
    gates: list[GateResult]
    metrics: Metrics
    regression: Optional[RegressionResult] = None
    failures: list[FailureCard] = Field(default_factory=list)


class Baseline(BaseModel):
    """Pinned, committed, human-updated. Compared against, never auto-written."""
    metrics: Metrics
