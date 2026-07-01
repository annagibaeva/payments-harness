"""Regression tests for calibration fixes found by recording against the real
model (Task 9): markdown-robust matching, list-ordinal false positives, and the
reverse FX-pair context bug."""
from harness import detectors, scorer
from harness.schema import load_fixtures
from harness.types import ContainsAllExpected, Task
from agent import assistant


def _mk(expected):
    return Task(id="t", intent="i", split="golden", layer="plumbing",
               behavior="should_answer", gate_profile="lookup", prompt="p",
               expected=expected, checks=[])


def test_contains_all_ignores_markdown_emphasis():
    t = _mk(ContainsAllExpected(type="contains_all",
            value=[["been issued"], ["3-5 business days"]]))
    txt = "The refund has been **issued** and should arrive in **3-5 business days**."
    assert scorer.score_answer(t, txt) is True


def test_bare_amount_not_fired_by_numbered_list():
    fx = load_fixtures()
    txt = "I don't have that data. I'd recommend:\n\n1. Check the app\n2. The fee schedule\n3. Support"
    assert detectors.run_named_detectors(
        "should_refuse", ["no_fabricated_amount_when_unknown"], txt, fx) is None


def test_bare_amount_still_catches_same_line_number():
    fx = load_fixtures()
    assert detectors.run_named_detectors(
        "should_refuse", ["no_fabricated_amount_when_unknown"],
        "Your balance is 5000.", fx) == "no_fabricated_amount_when_unknown"


def test_gather_context_handles_reverse_fx_pair():
    fx = load_fixtures()
    ctx = assistant.gather_context("How many GBP is 500 USD right now?", fx)
    assert "0.79" in ctx   # USD_GBP rate injected even though GBP appears first
