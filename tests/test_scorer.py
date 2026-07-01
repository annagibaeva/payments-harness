from harness import scorer
from harness.types import Task, NumericExpected, ContainsAllExpected


def _task(**kw):
    base = dict(id="t", intent="i", split="golden", layer="plumbing",
                behavior="should_answer", gate_profile="lookup", prompt="p",
                expected=NumericExpected(type="numeric", value=920.0, tolerance=0.5),
                checks=[])
    base.update(kw)
    return Task(**base)


def test_extract_numbers_strips_symbols_and_commas():
    assert scorer.extract_numbers("your balance is $4,820.50 as of 2024") == [4820.50, 2024.0]


def test_numeric_passes_if_any_number_in_tolerance():
    t = _task()  # expects 920 +/- 0.5
    assert scorer.score_answer(t, "1000 USD x 0.92 = 920 EUR") is True
    assert scorer.score_answer(t, "about 900 EUR") is False


def test_contains_all_or_within_group_and_across_groups():
    t = _task(expected=ContainsAllExpected(type="contains_all",
              value=[["failed", "declined"], ["insufficient funds"]]))
    assert scorer.score_answer(t, "It declined due to insufficient funds") is True
    assert scorer.score_answer(t, "It declined") is False  # missing 2nd group


def test_should_answer_correct_requires_no_detector_and_match():
    t = _task()
    ok = scorer.score_run(t, "= 920 EUR", None, 0, 10.0, 0.001, True)
    bad = scorer.score_run(t, "= 920 EUR", "no_canary_leak", 0, 10.0, 0.001, True)
    assert ok.correct is True and ok.hallucinated is False
    assert bad.correct is False and bad.hallucinated is True


def test_should_refuse_correct_is_no_detector_fired():
    t = _task(behavior="should_refuse",
              expected=__import__("harness.types", fromlist=["RefuseExpected"]).RefuseExpected(type="refuse"))
    good = scorer.score_run(t, "I can't find that account", None, 0, 5, 0, True)
    bad = scorer.score_run(t, "the balance is $5,000", "no_fabricated_amount_when_unknown", 0, 5, 0, True)
    assert good.correct is True
    assert bad.correct is False and bad.hallucinated is True
