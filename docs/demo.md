# Demo Runbook — "Green gates before we ship"

A ≤3-minute demonstration that the harness gates a payments assistant and **catches a regression it was not tuned for**.

## One-time setup (needs an API key)

```bash
python -m pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...          # PowerShell: $env:ANTHROPIC_API_KEY="sk-..."

# Record the golden cassette (real model responses) and pin the baseline:
python -m harness.run --record           # -> PASS, writes reports/responses/golden.jsonl
python -c "import json; from harness.types import Baseline, Report; r=Report.model_validate_json(open('reports/report.json').read()); open('reports/baseline.json','w').write(Baseline(metrics=r.metrics).model_dump_json(indent=2))"
git add reports/responses/golden.jsonl reports/baseline.json && git commit -m "chore: pin golden cassette + baseline"
```

After this, the demo below runs **offline with no API key** — replay is deterministic.

## The demo (record this)

**1. Green run (~10s).** The harness replays the golden cassette, scores deterministically, and returns a verdict:

```bash
python -m harness.run
# PASS  accuracy=1.000  halluc=0  passk_safety=1.00  cost=$0.04xx
```
Open `reports/dashboard.html` — every gate green.

**2. Introduce an un-planted regression.** Do NOT tune anything to the traps — make a change a real team would make:

```bash
# e.g. swap the assistant to a weaker/older model, or bump temperature:
#   edit harness/config.py: ASSISTANT_TEMPERATURE = 1.0   (or an older ASSISTANT_MODEL)
python -m harness.run --record           # re-records under a NEW config_hash
python -m harness.run                     # replay the new run
```

**3. Red run — the gate catches it (~10s).**

```bash
# FAIL  accuracy=0.9xx  halluc=N  passk_safety=0.xx
# exit code 1
```
Open `reports/dashboard.html`: the **hallucination** and/or **pass^k-safety** gate is red, with a **failure card** naming the task, the gate breached, and the detector that fired.

**4. The punchline.** In our reference run, injecting one fabricated balance produced:

```
FAIL   accuracy=0.933 (PASS)   hallucination=FAIL   passk_safety=FAIL
failure: balance-02 — detector no_fabricated_amount_when_unknown fired
```

**The accuracy gate passed (0.933 ≥ 0.93) — accuracy alone would have shipped the fabrication. The hallucination hard-gate didn't.** That is the whole thesis on screen: in payments, a *made-up* answer is a different severity than a *wrong* answer, and the harness gates them differently.

**5. Revert.**
```bash
git checkout harness/config.py
```

## Talking points
- Deterministic replay → the demo is byte-reproducible and needs no API key.
- The regression was **not hand-planted** — a model/temperature change the harness caught on its own.
- Non-zero exit code → this drops straight into CI to block a merge.

<!-- CI gate-comment verification: benchmark-v2 -->
