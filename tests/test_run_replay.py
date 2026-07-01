# tests/test_run_replay.py
from pathlib import Path
from harness import run, config, cassette
from harness.schema import validate_all
from harness.types import Response


def _seed_perfect_cassette(path: Path, cfg: str, taskset, fixtures):
    # canned correct responses so replay yields a green run with no API calls
    canned = {
        "numeric": lambda t: f"The answer is {t.expected.value}.",
        "contains_all": lambda t: " ".join(g[0] for g in t.expected.value),
        "refuse": lambda t: "I can't help with that / no such account.",
    }
    for t in taskset.tasks:
        text = canned[t.expected.type](t)
        for r in range(config.K):
            cassette.append(path, Response(task_id=t.id, run=r, text=text,
                            latency_ms=500, cost_usd=0.0005, from_cassette=True), cfg)


def test_replay_green_run(tmp_path, monkeypatch):
    ts, fx = validate_all()
    cfg = config.config_hash(ts.version, fx.version)
    cassette_path = tmp_path / "responses.jsonl"
    _seed_perfect_cassette(cassette_path, cfg, ts, fx)
    monkeypatch.setattr(config, "RESPONSES_DIR", tmp_path)
    monkeypatch.setattr(config, "REPORT_JSON_PATH", tmp_path / "report.json")
    monkeypatch.setattr(config, "DASHBOARD_PATH", tmp_path / "dash.html")
    monkeypatch.setattr(config, "BASELINE_PATH", tmp_path / "nobaseline.json")
    monkeypatch.setattr(run, "_cassette_file", lambda: cassette_path)
    code = run.run(record=False)
    assert code == 0
    assert (tmp_path / "report.json").exists()
