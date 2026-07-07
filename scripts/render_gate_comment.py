"""Renders `reports/report.json` (a serialized `harness.types.Report`) into a
GitHub-flavored markdown PR comment.

Stdlib only — no new dependencies. Used by the `release-gates` CI workflow to
post/update a sticky PR comment so a red gate is impossible to miss.

Usage:
    python scripts/render_gate_comment.py [path/to/report.json]

Writes markdown to stdout. Always exits 0 (including for FAIL verdicts) —
rendering must never fail the job; the harness step already sets job status.
"""
from __future__ import annotations

import json
import sys

MARKER = "<!-- release-gates-comment -->"
ACTUAL_TRUNCATE_LEN = 200


def _status_icon(gate: dict) -> str:
    if gate["passed"]:
        return "✅ PASS"
    if gate["blocking"]:
        return "❌ FAIL"
    return "⚠️ WARN"


def render(report: dict) -> str:
    lines: list[str] = [MARKER]

    verdict = report["verdict"]
    if verdict == "PASS":
        lines.append("## Release gates: PASS ✅")
    else:
        lines.append("## Release gates: FAIL ❌")

    lines.append("")
    lines.append("| Gate | Observed | Threshold | Status |")
    lines.append("| --- | --- | --- | --- |")
    for gate in report.get("gates", []):
        lines.append(
            f"| {gate['name']} | {gate['observed']} | {gate['threshold']} | {_status_icon(gate)} |"
        )

    regression = report.get("regression")
    if regression and regression.get("regressions"):
        lines.append("")
        lines.append("**Regressions**")
        for reg in regression["regressions"]:
            lines.append(f"- {reg}")

    failures = report.get("failures", [])
    if failures:
        lines.append("")
        lines.append("**Failures**")
        for card in failures:
            actual = card.get("actual", "")
            if len(actual) > ACTUAL_TRUNCATE_LEN:
                actual = actual[:ACTUAL_TRUNCATE_LEN] + "..."
            lines.append("")
            lines.append(f"- `{card['task_id']}` — gate breached: `{card['gate_breached']}`")
            lines.append(f"  - why: {card['why']}")
            lines.append(f"  - actual: {actual}")

    metrics = report.get("metrics", {})
    lines.append("")
    lines.append(
        f"---\n"
        f"benchmark: `{metrics.get('benchmark_version', '')}` · "
        f"fixtures: `{metrics.get('fixtures_version', '')}` · "
        f"config: `{metrics.get('config_hash', '')}`"
    )

    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = argv[0] if argv else "reports/report.json"

    with open(path, encoding="utf-8") as f:
        report = json.load(f)

    output = render(report)
    try:
        sys.stdout.write(output)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(output.encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
