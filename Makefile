.PHONY: setup validate eval test

setup:
	python -m pip install -r requirements.txt

# Validate the benchmark contracts (fail loud on any typo / bad detector / version mismatch)
validate:
	python -m harness.schema

# Phase 0: eval == validate (empty pass). Becomes the full pipeline in integration.
eval:
	python -m harness.run

test:
	python -m pytest

# --- Windows (no make) equivalents ---
# python -m pip install -r requirements.txt
# python -m harness.schema
# python -m harness.run
# python -m pytest
