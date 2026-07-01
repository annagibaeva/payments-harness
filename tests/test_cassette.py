from pathlib import Path
from harness import cassette
from harness.types import Response


def test_append_then_load_roundtrip(tmp_path: Path):
    p = tmp_path / "c.jsonl"
    r = Response(task_id="t1", run=0, text="hello", latency_ms=12.0, cost_usd=0.001)
    cassette.append(p, r, config_hash="abc123")
    loaded = cassette.load(p, config_hash="abc123")
    assert cassette.key("t1", 0, "abc123") in loaded
    assert loaded[cassette.key("t1", 0, "abc123")].text == "hello"


def test_load_ignores_other_config_hash(tmp_path: Path):
    p = tmp_path / "c.jsonl"
    cassette.append(p, Response(task_id="t1", run=0, text="x", latency_ms=1, cost_usd=0), "hashA")
    assert cassette.load(p, "hashB") == {}


def test_load_missing_file_returns_empty(tmp_path: Path):
    assert cassette.load(tmp_path / "nope.jsonl", "h") == {}
