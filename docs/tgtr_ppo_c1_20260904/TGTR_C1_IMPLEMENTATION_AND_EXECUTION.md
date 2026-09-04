# TGTR-PPO C1 implementation and execution freeze

## Authorized scope

C1 implements the default-off 24-stream synchronized topology sampler and the TGTR actor transaction, then runs five training-only same-rollout source-state audits (2201--2205). It does not run a fresh-seed pilot, formal evaluation, held-out evaluation, return-based tuning, or automatic continuation.

## Source-state migration

The five source runtime checkpoints were produced with four environments. C1 restores only their model and Adam states, then initializes a new deterministic 24-stream training rollout. It deliberately does not restore the incompatible four-environment runtime state. Each ordinary/TGTR pair starts from the same restored model/optimizer and consumes the same immutable batch hash.

## Synchronized collection

Streams 0--11 are nominal; streams 12--23 are fixed pairs for F0, TE, TL, DS, DL, and CP. The first six nominal streams and first stream in each failure pair are design data; the rest are certificate data. Group/split labels remain outside observations and all evaluation interfaces.

## Actor transaction

Each PPO epoch first creates the ordinary Adam actor candidate and ordinary critic update. TGTR identifies harmed failure groups on design streams, projects the actor displacement onto nominal, active-group, and overall surrogate halfspaces, and applies the frozen backtracking sequence. Certificate acceptance requires nonnegative held-stream surrogate change for all seven groups and pooled failures plus per-group full-categorical KL below the clip-derived cap. A rejected actor transaction restores actor parameters and actor Adam slots exactly while retaining the ordinary critic update. A nonzero projected step retains the ordinary Adam proposal slots.

Because the implementation evaluates float32 neural-network surrogates, the mathematical nonnegativity comparison uses a fixed `1e-7` numerical tolerance. This is only a round-off allowance, is below the reported mechanism effects, and is not a tunable performance margin.

## Output and stopping rule

The cloud job writes one JSON result per source state, a CSV summary, `TGTR_C1_GATE_DECISION.json`, and `TGTR_C1_FINAL_VERDICT.md`. The only outcomes are `TGTR_C1_MECHANISM_PASS`, `TGTR_C1_INCONCLUSIVE`, or `TGTR_C1_NO_GO`. None authorizes a fresh-seed pilot automatically.
