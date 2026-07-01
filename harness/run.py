"""Runner entry point.

Phase 0: this only validates the contracts (empty pass) so `make eval` has a
working end-to-end path from day one. The full pipeline
(cassette -> agent -> scorer -> detectors -> gates -> regression -> report) is
wired here during integration (PRD Phase 2 / milestones M3-M6).
"""
from __future__ import annotations

import sys

from . import schema


def main(argv: list[str] | None = None) -> int:
    try:
        taskset, fixtures = schema.validate_all()
    except Exception as exc:  # noqa: BLE001 - surface any load/validation error
        print(f"VALIDATION FAILED\n{exc}", file=sys.stderr)
        return 1
    print(schema._summary(taskset, fixtures))
    print("Phase 0: contracts validated. Runner pipeline not yet implemented "
          "(built during integration — see PRD §8).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
