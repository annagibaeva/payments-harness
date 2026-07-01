# Case Study — Setting Release Gates for a Fintech AI Assistant

> Draft for the portfolio narrative. Written in the PM's voice; tune freely.

## The judgment call, first

In payments, **a wrong answer and a made-up answer are not the same failure.** A wrong-but-honest "I'm not sure" is survivable; a *confidently fabricated* balance, fee, or FX rate is a trust-and-compliance incident. So I did not build one "quality score." I built **two gates with different tolerances**: accuracy tolerates one honest miss; hallucination tolerates none.

That single decision — separating severity — is what turns a generic eval into a payments release control. Everything else follows from it.

## What I built

A reproducible harness that runs a 15-task payments benchmark against an assistant, scores every response **deterministically** (no LLM grading anywhere on the gate path), and returns one **PASS/FAIL** verdict against four gates — accuracy, hallucination (zero-tolerance hard gate), pass^k reliability, and cost — plus a version-aware regression check against a pinned baseline. Non-zero exit on failure, so it drops into CI. (Full spec: [PRD](PRD-payments-assistant-reliability-harness.md); every threshold justified in [threshold-rationale.md](threshold-rationale.md).)

## The moment it proved itself

I injected a single fabricated balance into one adversarial task and re-ran:

```
FAIL   accuracy = 0.933 (PASS)   hallucination = FAIL   pass^k-safety = FAIL
failure: balance-02 — detector "no_fabricated_amount_when_unknown" fired
```

**The accuracy gate passed. Accuracy alone would have shipped the fabrication.** The hallucination hard-gate caught it. That is the severity-split argument, demonstrated — not asserted.

## The tradeoffs I made (and what I gave up)

- **Determinism over an LLM judge.** LLM outputs aren't reproducible, so I kept every scorer a pure function and moved reproducibility into a **cassette** of recorded responses. I gave up "nuanced tone grading" in v1 — deliberately — to make the gate byte-reproducible and defensible. The judge is a documented V2 add-on, off the gate path.
- **Zero-tolerance on hallucination, one-miss tolerance on accuracy.** False alarms on the hard gate are cheap; a fabricated financial fact in production is not. I biased toward blocking.
- **The detector is the load-bearing risk, so I validated it first.** A zero-tolerance gate is only as good as its detector. Before trusting it, I required **≥95% recall on injected fabrications and ≤5% false-positives on honest refusals** on a hand-labeled set — and treated that as a build-blocking gate. (It cleared at 100% / 0%.) You cannot measure catch-rate from a well-behaved assistant that never fabricates — so I measured it on injected fabrications, not the live benchmark.
- **Anti-gaming by construction.** The benchmark is weighted 10 should-answer / 5 should-refuse, so an assistant can't score a clean hallucination sheet by refusing everything — blanket-refusal fails ~two-thirds of tasks.
- **Cost blocks, latency warns.** Cost is deterministic (from token usage) so a regression is real signal → it blocks. Latency against a remote API is CI-flaky → it warns, doesn't block, in v1.
- **Honest about scope.** 15 tasks is small; the *safety* signal is effectively ~6 adversarial tasks. I labelled plumbing vs safety explicitly rather than overclaiming statistical power, and scoped growth to V2. v1 proves the *methodology* on mock data — not production safety.

## What a reviewer or regulator gets

A green/red verdict a PM can defend, a failure card that shows exactly what broke and why, and a reproducible run that a regulator's model-risk process could file as control evidence. "We tested it" becomes "here are the green gates."

## What I'd do next (V2/V3)

Per-intent SLAs, a 50+ task set grown from real incidents, model/prompt A/B gating on a cost×accuracy×hallucination Pareto, an auditable attestation artifact, and a **Failure Knowledge Bank** that turns every caught failure into new tests + new detectors — informing humans and tests, never auto-patching the customer-facing assistant.
