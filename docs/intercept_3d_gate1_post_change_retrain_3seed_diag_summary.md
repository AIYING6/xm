# Gate 1 Post-Change Three-Seed Retraining Diagnostic

Last updated: 2026-07-18

## Purpose

Check whether the frozen dropout-relay bottleneck protocol remains trainable after the Gate 1 communication-feasibility changes.

This is still a development diagnostic, not a paper result, because it uses only three continuation PPO updates from existing checkpoints.

## Gate 1 Semantic Changes Covered

The diagnostic runs after these changes:

- graph direction convention: `A[receiver, sender] = 1`;
- task-support edges require delivered physical communication;
- 3DOF actor intent-context broadcast disabled;
- delayed communication uses a pending-message queue;
- target information uses per-agent target-message caches;
- multi-hop target information advances one hop per delay cycle;
- task-chain closure requires executor-side target information.

## Training Protocol

Output:

```text
results/intercept_3d_gate1_post_change_retrain_3seed_diag/
```

Methods:

- `single`;
- `multi_relation`.

Seeds:

- `0, 1, 2`.

Training:

- resume from the existing 60-update dropout-relay diagnostic checkpoints;
- 3 continuation PPO updates;
- 1 vector environment;
- 16 rollout steps;
- strict target sensing enabled;
- agent target-information bottleneck enabled;
- communication dropout randomized from `0.00` to `0.30`;
- message delay randomized from `0` to `2`;
- node-failure curriculum enabled.

Evaluation:

- scenario: `dropout030_relay_failure`;
- episodes: `20` matched episodes per seed;
- base seed: `884001`;
- checkpoint: `actor_critic_update_0003.pt`.

## Aggregate Result

| Method | Success | Recovery | Timeout | Tracking During Failure | Connectivity During Failure |
|---|---:|---:|---:|---:|---:|
| `single` | `35.0%` | `35.0%` | `63.3%` | `44.7%` | `18.2%` |
| `multi_relation` | `95.0%` | `95.0%` | `5.0%` | `95.6%` | `33.2%` |

Seed-aware statistics:

- `multi_relation - single` task success: `+60.0 pp`, 95% CI `[+16.7, +90.0] pp`;
- `multi_relation - single` post-failure recovery: `+60.0 pp`, 95% CI `[+16.7, +90.0] pp`;
- restricted mean recovery steps: `-125.60`, 95% CI `[-189.77, -34.88]`;
- tracking during failure: `+50.9 pp`, 95% CI `[+13.8, +76.1] pp`;
- connectivity during failure: `+14.9 pp`, 95% CI `[+2.8, +22.8] pp`.

## Interpretation

The new communication-feasible semantics remain trainable. More importantly, the multi-relation method remains consistently stronger than the single union-graph baseline across all three seeds in this small retraining diagnostic.

The result also shows why a larger post-Gate-1 diagnostic is justified before five-seed formal training. The current continuation budget is too small and does not include validation checkpoint selection.

## Decision

Proceed to a 20-update post-Gate-1 diagnostic with validation checkpoint selection before any formal five-seed run.

Recommended next protocol:

- methods: `single`, `multi_relation`;
- seeds: `0, 1, 2`;
- updates: `20`;
- save interval: `5`;
- validation checkpoint selection on `dropout030_relay_failure`;
- disjoint test split;
- only add `no_graph` after the single-vs-multi signal remains stable.
