"""Payments Assistant Eval & Reliability Harness.

Phase 0 delivers the *contracts* every other component builds against:
  - config.py  : pinned models, thresholds, detector names, cassette key
  - types.py   : pydantic models for tasks, fixtures, responses, scores, report
  - schema.py  : load + validate tasks.yaml / fixtures.yaml (fail loud)

Downstream modules (cassette, scorer, detectors, gates, regression, report,
runner) are built in parallel against these types — see docs/PRD §8.
"""

__all__ = ["config", "types", "schema"]
