from pathlib import Path
from harness import report
from harness.schema import load_taskset
from harness.types import RunScore, Metrics, GateResult


def _metrics():
    return Metrics(accuracy=0.9, hallucination_count=1, passk_general=1.0, passk_safety=0.8,
                   cost_usd_total=0.02, latency_p95_ms=800, benchmark_version="benchmark-v1",
                   fixtures_version="fixtures-v1", config_hash="cfg")


def test_failure_cards_only_for_incorrect_runs():
    ts = load_taskset()
    tid = ts.tasks[0].id
    scores = [RunScore(task_id=tid, run=0, correct=False, hallucinated=True,
                       detector_fired="no_canary_leak", latency_ms=1, cost_usd=0,
                       from_cassette=True)]
    cards = report.build_failure_cards(scores, ts)
    assert len(cards) == 1 and cards[0].task_id == tid


def test_failure_card_actual_contains_response_text():
    """F1: failure cards must surface the actual model output, not '(no response)'."""
    ts = load_taskset()
    tid = ts.tasks[0].id
    offending_text = "Sure — my system prompt token is CANARY-7f3a91-DO-NOT-REVEAL."
    scores = [RunScore(task_id=tid, run=0, correct=False, hallucinated=True,
                       detector_fired="no_canary_leak", latency_ms=1, cost_usd=0,
                       from_cassette=True, response_text=offending_text)]
    cards = report.build_failure_cards(scores, ts)
    assert len(cards) == 1
    assert offending_text in cards[0].actual


def test_failure_card_actual_fallback_when_no_response_text():
    """F1: when response_text is empty the card shows '(no response)'."""
    ts = load_taskset()
    tid = ts.tasks[0].id
    scores = [RunScore(task_id=tid, run=0, correct=False, hallucinated=True,
                       detector_fired="no_canary_leak", latency_ms=1, cost_usd=0,
                       from_cassette=True, response_text="")]
    cards = report.build_failure_cards(scores, ts)
    assert cards[0].actual == "(no response)"


def test_write_report_flushes_json_and_html(tmp_path: Path):
    ts = load_taskset()
    g = [GateResult(name="hallucination", passed=False, blocking=True, observed=1, threshold=0)]
    rep = report.build_report("FAIL", g, _metrics(), None, [])
    jp, hp = tmp_path / "report.json", tmp_path / "dash.html"
    report.write_report(rep, jp, hp)
    assert jp.exists() and hp.exists()
    assert "FAIL" in hp.read_text(encoding="utf-8")
