# T6 Final Decision — Support-to-Decision Structure Discovery

## Frozen history

T1–T5 remain unchanged. In particular, T5's final result is `D — NO_GO`; it is not converted to a pass by this audit. T6 used no training, rollout, environment interaction, or new checkpoint.

## Four-family outcome

| Family | Outcome | Interpretation |
|---|---|---|
| A: support sensitivity magnitude | PASS | Cross-condition, matched GOOD-over-WEAK signal. |
| B: role-specific response | FAIL | Relay is a pre-specified counterexample. |
| C: support-state action separation | PASS | Corroborating broad state-to-decision structure. |
| D: transition-local adaptation | FAIL | GOOD is neither faster nor more settled. |

## Decision

**D2 — MODERATE_DECISION_STRUCTURE_SIGNAL**

The sole `PRIMARY_ALGORITHMIC_TARGET` is:

> **Calibrated actor-legal support sensitivity** — whether a policy uses its already legal support state to make conditionally differentiated decisions, without prescribing uniform sensitivity, role-specific behavior, or rapid action switching.

This target is selected because Family A passes its fixed matched and cross-condition checks, both GOOD seeds exceed both WEAK seeds, and its five-seed descriptive rank association with F0/OOD return is positive. Family C is corroboration only. B and D are negative evidence and explicitly rule out role-specific and transition-speed claims.

## What this does not authorize

T6 does **not** authorize an algorithm design, loss, architecture, implementation, new telemetry, rollout, training, held-out run, canonical run, or causal claim. A separately authorized pre-training design review would still need to test novelty, information legality, failure modes, and a prospective falsification contract before any development run.
