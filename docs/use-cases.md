# Practical Use Cases — When a Payments-Assistant Reliability Harness Earns Its Keep

> BRD-ready scenarios. Companies named (Airwallex, Stripe, Wise) are **illustrative
> examples** of the kind of payments business that ships a customer-facing AI
> assistant — not a targeting claim. Each scenario: the trigger, what the harness
> does, which gate fires, and the business outcome.

## At a glance

| # | Situation | Primary user | Gate(s) that fire | Business value |
|---|-----------|--------------|-------------------|----------------|
| 1 | Every code change to the assistant | Applied-AI eng | All (in CI) | No unsafe change reaches customers |
| 2 | Foundation-model upgrade | PM + eng | Accuracy, pass^k safety | Capture new-model gains without regressing safety |
| 3 | "Make it more helpful" prompt edit | PM | Hallucination, authz detector | Data-leak / wrong-answer incident avoided |
| 4 | New intent / feature launch | PM | New tasks + all gates | Feature ships with a safety bar, not vibes |
| 5 | Cost optimization (cheaper model) | Eng + Finance | Cost (block), Accuracy | Cost decisions on evidence, not hope |
| 6 | Regulator / audit request | Risk & Compliance | Attestation artifact | Auditable model-risk control |
| 7 | Post-incident hardening | PM + eng | Test-set growth loop | Same failure can't silently recur |
| 8 | Production drift after launch | SRE / Risk | Canary hallucination gate | Runtime safety net, limited blast radius |

---

## 1. Pre-release gate on every change (the default use)
**Trigger:** an engineer at a payments company edits the support assistant's system prompt, tools, or model, and opens a PR.
**What happens:** CI runs the harness against the 15-task benchmark. A red hallucination or accuracy gate **blocks the merge**; the gate report is posted on the PR.
**Outcome:** the team stops approving assistant changes on manual spot-checks. "Is this safe to ship?" is answered by a green/red verdict a PM can defend — every single change, automatically.

## 2. Foundation-model upgrade
**Trigger:** the model provider releases a newer/cheaper model; the team wants the support copilot to use it.
**What happens:** the harness runs the candidate model. Accuracy holds, **but pass^k safety drops below 100%** — the assistant's injection resistance became intermittent under the new model. Upgrade is **blocked pending a guardrail fix**.
**Outcome:** the company adopts model improvements on its own schedule, with proof that safety didn't silently regress in the upgrade — the exact risk that makes teams afraid to upgrade at all.

## 3. A "more helpful" prompt tweak backfires
**Trigger:** a PM loosens the system prompt to make the assistant answer more freely.
**What happens:** the harness catches that the assistant now returns **another customer's account balance** when asked (a cross-account authorization leak). The `no_out_of_scope_amount` detector fires → **hard-gate FAIL** in CI, before merge.
**Outcome:** a reportable data-exposure incident is caught in a pull request instead of in production — arguably the single most expensive class of bug this prevents.

## 4. New intent / feature launch
**Trigger:** Airwallex-style business adds "when will my international transfer arrive?" to the assistant.
**What happens:** new labeled tasks are added — including a **should-refuse trap** for corridors the assistant has no ETA data for (so it can't invent one). The harness sets the release gate for the new capability.
**Outcome:** the feature ships behind a measured safety bar. The benchmark grows with the product, so coverage never lags behind what customers can actually ask.

## 5. Cost optimization
**Trigger:** at scale, inference cost matters; Finance asks whether the assistant can move to a smaller/cheaper model.
**What happens:** the harness quantifies the trade — the cheaper model saves ~40% cost **but drops FX-quote accuracy below the gate**. The **cost gate** (deterministic) and the accuracy gate together frame the decision.
**Outcome:** a build-vs-cost call made on evidence. The organization never trades a hallucination increase for margin without seeing it — and can re-run the moment a cheaper model *does* pass.

## 6. Regulator / audit evidence
**Trigger:** Risk must demonstrate to a regulator (e.g., MAS, FCA, ASIC) that the customer-facing AI has validated controls.
**What happens:** every release emits a **timestamped attestation** — task-set version, model versions, config hash, verdict, and metrics — to an append-only store (PRD §9.4).
**Outcome:** "here is the control, here is the evidence, here is the exact version that shipped." Model-risk governance (SR 11-7-style validation, EU AI Act control evidence) backed by an artifact, not a slide.

## 7. Post-incident hardening (the learning loop)
**Trigger:** a customer complaint reveals the assistant quoted a **made-up fee** for a payment corridor not in the fee schedule.
**What happens:** that exact failure becomes a **new permanent adversarial task** plus a fabrication-detector case. The benchmark now guards that failure mode on every future run.
**Outcome:** the same class of mistake cannot silently recur. Each incident makes the gate permanently stronger — the harness compounds in value over time rather than going stale.

## 8. Production drift after launch (V3)
**Trigger:** months post-GA, the upstream model is silently updated by the provider.
**What happens:** live monitoring runs the gate on a canary slice; **hallucination-gate breaches appear** → **automatic rollback** before broad customer exposure.
**Outcome:** a runtime safety net. Drift that no PR introduced — and that offline testing alone would miss — is caught with a limited blast radius.

---

## How to frame this in a BRD

- **Problem:** customer-facing payments assistants can give *confidently wrong* financial answers; today teams ship them on manual spot-checks and vibes, with no defensible ship/no-ship control.
- **Business risk if unaddressed:** customer-trust damage, mis-quoted fees/FX, data-exposure incidents, and no auditable evidence for regulators.
- **Capability:** an automated release gate that blocks any assistant change breaching accuracy, hallucination, reliability, or cost thresholds — and produces an audit artifact.
- **Who benefits:** PMs (ship confidence), engineers (regression safety in CI), Risk/Compliance (auditable control), Finance (evidence-based cost decisions), and — indirectly but most importantly — **customers**, who never receive a fabricated financial answer.
