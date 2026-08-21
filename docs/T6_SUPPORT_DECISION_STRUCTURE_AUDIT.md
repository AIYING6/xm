# T6 — Good-vs-Weak Support-to-Decision Structure Audit

## Status

**Completed, zero-training, existing-assets-only.** This audit preserves all T1–T5 conclusions, including the T5 `NO_GO`. It neither constructed the environment nor called `reset`/`step`, and it made no optimizer, checkpoint, or policy update.

## Frozen scope

- GOOD: seeds 2202 and 2204; WEAK: seeds 2203 and 2205; INTERMEDIATE: seed 2201.
- Assets: frozen T1 final 1M UTR-SG checkpoints, recorded step telemetry, and frozen T2 seed-level outcomes.
- Decision families: exactly A–D below. No fifth candidate family was tested.
- Evaluation families: F0, timing OOD, and duration OOD. Nominal and compound scenarios were not used to manufacture a positive result.
- Support quality: a fixed actor-legal summary of attacker direct detection, inbound communication, inverse inbound age, inverse cache age, and cache confidence; threshold `0.50` fixed before scanning.

## Data integrity and legality

Each of the five checkpoints had exactly 116,728 parameters. The scan used 3,600 balanced frozen samples per seed (1,800 future-support-continuity labels per class), totaling 18,000 forward samples. Actor inputs were restricted to existing local observation and graph tensors. Seed rank, future continuity, condition, and T2 return were diagnostic labels only; `share_obs`, global topology/path state, future state, and simulator failure truth were excluded.

The read-only output is `results/development/t6_support_decision_structure_audit_run1/t6_decision_structure_audit.json`.

## Fixed controls

GOOD–WEAK comparisons were made inside recorded-state strata: role, condition family, phase, task progress, local topology label, support bin, expected-action-norm bin, and direct-target visibility. The results are therefore not merely unmatched differences in episode phase, role mix, or action magnitude.

## Family summary

| Family | Frozen question | Result | Evidence boundary |
|---|---|---:|---|
| A | Does actor-legal support change policy distribution more in GOOD than WEAK after matching? | PASS | Decision-use signal, not a causal method proof. |
| B | Is the response consistently role-specific? | FAIL | Relay gives the opposite GOOD–WEAK direction. |
| C | Do support-present and support-absent states separate decisions more in GOOD? | PASS | Corroborating structure, not a second target. |
| D | Do GOOD policies adapt faster and settle better after support transitions? | FAIL | GOOD is slower and less settled. |

## Cross-condition and seed checks

Family A's matched GOOD-minus-WEAK sensitivity gap was `+0.0765` across 121 matched cells: F0 `+0.0768`, timing `+0.0737`, duration `+0.0788`. Both GOOD seeds exceeded both WEAK seeds (`0.1222`, `0.1620` versus `0.0261`, `0.0671`). Seed-level sensitivity had Spearman `+0.80` with each of T2 `J_F0`, `J_OOD_mean`, and `J_OOD_worst` (five-seed descriptive association only).

Family C also had positive matched gaps in all three conditions: F0 `+0.1172`, timing `+0.0896`, duration `+0.0681`. It is corroboration, not a second algorithm claim.

## Limitation and decision boundary

This is a five-seed, offline, observational audit. It does not establish that increasing sensitivity improves performance, that the association is causal, or that a new objective is justified. T6 authorizes no algorithm design, implementation, rollout, or training. The final decision is in `T6_FINAL_DECISION.md`.
