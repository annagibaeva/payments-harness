"""Payments assistant-under-test package.

Built during M3 (agent + mock data layer). The assistant is a thin wrapper over
a cheap model (config.ASSISTANT_MODEL) with a canary'd system prompt and
read-only tool access to the mock data layer sourced from evals/fixtures.yaml.
"""
