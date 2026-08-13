# Phase S3-R1 Unexposed-Episode Root-Cause Audit

**Protocol:** `PHASE-S3-R1`  
**Artifact class:** DEVELOPMENT_ONLY / READ-ONLY AUDIT  
**Training:** none

## Scope

This audit examines the three `failure_exposed=0` episodes identified by the
completed S3-R evaluation for `Full / training seed 1503`. It uses the S3-R
raw episode table and the paired nominal rows. No episode was removed, repaired,
re-scheduled, or re-evaluated.

## Finding

All three misses have the same root cause:

| S3-R episode ID | Failure terminal step | Nominal terminal step | Failure scheduled | Failure active steps | Terminal reason | Classification |
|---:|---:|---:|---|---:|---|---|
| 340002 | 34 | 34 | yes | 0 | collision | natural collision before failure onset |
| 340063 | 34 | 34 | yes | 0 | collision | natural collision before failure onset |
| 340079 | 34 | 34 | yes | 0 | collision | natural collision before failure onset |

The frozen failure onset is step 44. Every missed pair terminates at step 34,
ten steps before onset, with collision in both nominal and failure conditions.
The failure intervention therefore had no opportunity to become active. This
is policy/environment behavior, not an evaluator scheduling defect.

## Decision

`S3-R1 = NATURAL-PRE-FAILURE-TERMINATION / EVALUATOR-BUG-NO-GO`.

The three episodes must remain part of the all-planned-pairs exposure audit.
They must not be discarded to force 100% exposure, and the failure onset must
not be moved earlier in response to this result. S3-R therefore remains
`INCONCLUSIVE` for strict shared-tape comparison, while the exposure issue is
now explained rather than unresolved.

## Learnability diagnosis from archived logs

The final 100-update reward slopes were small and mixed, not a consistent
upward trajectory:

| Method | Seed | Final reward mean | Final-window slope |
|---|---:|---:|---:|
| MAPPO | 1501 | -0.0279 | 0.00033 |
| MAPPO | 1502 | 0.0186 | 0.00047 |
| MAPPO | 1503 | -0.0080 | -0.00014 |
| Matched SG | 1501 | 0.0595 | 0.00004 |
| Matched SG | 1502 | 0.0152 | 0.00037 |
| Matched SG | 1503 | 0.0104 | 0.00107 |
| Full | 1501 | 0.0669 | -0.00048 |
| Full | 1502 | -0.0159 | 0.00045 |
| Full | 1503 | 0.0123 | 0.00011 |

All final PPO diagnostics were finite. The logs do not support the simple
explanation that Full was still consistently improving at 200k steps. They
also do not establish stable nominal competence: Full's shared-tape nominal
means were 11.78, 38.34, and -14.76 for seeds 1501, 1502, and 1503.

Because training seed is the independent replication unit, these observations
are descriptive screening evidence, not episode-level inferential tests.

## Next gate

No S3-R rerun is justified by the three misses: the root cause is genuine
pre-failure collision, and re-running the same checkpoints would reproduce it.
The next action requires a separately frozen algorithm/learnability protocol.
It may consider a three-method equal-budget training diagnosis or a minimal
Full simplification, but it must not change S2 environment semantics, failure
onset, exposure estimand, seed set, or checkpoint selection based on these
results. S4 and Phase 3A remain NO-GO.
