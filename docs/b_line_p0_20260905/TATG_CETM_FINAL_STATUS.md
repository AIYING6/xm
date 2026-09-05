# TATG-CETM final status

**Final verdict:** `TATG_CETM_PILOT_NO_GO`.

## Scientific hypothesis

TATG-CETM tested whether explicit residuals of legal graph-topology transitions improve a fixed-UTR MAPPO actor beyond a current-snapshot actor and matched temporal controls. It did not alter the environment, reward, failure semantics, centralized critic, PPO objective, or offline evaluation boundary.

## Completed audit chain

- P0/P1 established the narrow structural information gap: a current topology snapshot can be ambiguous about a legal preceding transition, while one-step history removes that ambiguity.
- C1, C1.5, C2, C3, C3.5, C4 and C4.5 audited serialization, actor integration, runtime state, chronological PPO replay, reset isolation, outer rollout, and one legal update.
- The P1 audit recorded `TATG_P1_INFORMATION_GAP_PRESENT` in two separate state cohorts; it did not claim return improvement.

## Execution provenance

- V2/V3 execution is invalid for performance interpretation: all nine temporal trajectories exited before update 0 because the temporal snapshot code referenced the non-existent `UAVIntercept3DEnv.num_blue` attribute. The record is retained at `docs/tatg_mappo_pilot_p3_20260905/EXECUTION_REPAIR.md`.
- V4 repaired the GAE/interface path and completed the frozen four-arm, three-seed, 1M-step pilot. Source package: `TATG_MAPPO_PILOT_CLOUD_TRAINING_V4_GAE_REPAIR.zip`, SHA-256 `a8a6bc61a60a40be886454044852d596eb88e36f17855b59b8a218c24a533fab`.
- The fixed endpoint evaluator package is `TATG_MAPPO_PILOT_FIXED_ENDPOINT_EVALUATION_V2.zip`, SHA-256 `c5720891566c2eecf7fdb1a4b8390184845be452266a0029cacb97084d8e91e6`. Its frozen protocol evaluates update 3,907 only, on five conditions × 100 episodes × 12 seed-arm cells = 6,000 episodes and 60 seed-condition aggregates.
- The final V4 endpoint ledger/archive is not stored in this repository. The numerical values below are therefore marked **user-provided cloud provenance**, not locally recomputed evidence.

## Frozen P4 outcome — user-provided cloud provenance

| Arm | Mean non-nominal success | Mean nominal success |
| --- | ---: | ---: |
| UTR snapshot | 6.00% | 17.33% |
| Snapshot-GRU | 13.08% | not promoted to a claim |
| Zero-residual temporal control | 1.25% | not promoted to a claim |
| CETM | 2.58% | 1.00% |

The paired CETM-minus-UTR non-nominal differences were `0`, `0`, and `-10.25` percentage points. CETM nominal success was `-16.33` percentage points below UTR, violating the frozen `-5` percentage-point lower bound.

## Decision and boundary

The registered pilot rule required a positive CETM signal, no inferiority to either temporal control, no additional zero-success seed, and nominal non-inferiority. Those conditions were not met. This is a scientific no-go for the frozen CETM hypothesis, not an attribution to cloud hardware, concurrency, evaluator corruption, incomplete training, or the repaired GAE bug.

## Prohibited continuation

- No CETM-v2/TATG-v2, hyperparameter tuning, seed replacement, selective rerun, best-checkpoint selection, 10M escalation, or altered evaluation gate.
- No relabeling Snapshot-GRU as CETM success.
- No use of B-line deterministic reconfiguration as an A-line rescue component.

## Reusable, non-promoted assets

- P1 topology-transition information-gap result.
- Snapshot-GRU pilot observation only.
- Sequence-PPO and runtime-state infrastructure.
- Dynamic-topology 3D UAV environment and independent 6-UAV environment.
