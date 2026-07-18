# Gate 1 Post-Change Three-Seed Diagnostic

Last updated: 2026-07-18

## Purpose

This diagnostic checks whether existing 60-update checkpoints remain executable and directionally useful after the Gate 1 communication-feasibility changes:

- task-support edges require delivered physical communication;
- graph direction is `A[receiver, sender] = 1`;
- 3DOF intent-context broadcast is disabled;
- delayed communication uses a pending-message queue;
- target information uses per-agent target-message caches with path and hop count;
- task-chain closure requires executor-side target information.

This is a development diagnostic, not paper evidence.

## Protocol

Result directory:

```text
results/intercept_3d_gate1_post_change_3seed_diag/
```

Settings:

- scenario: `dropout030_relay_failure`;
- target policy: `straight`;
- strict target sensing: enabled;
- agent target-information bottleneck: enabled;
- checkpoint update: `60`;
- methods: `no_graph`, `single`, `multi_relation`;
- training seeds: `0, 1, 2`;
- matched evaluation episodes: `10` per seed;
- base seed: `882001`.

## Aggregate Result

| Method | Success | Recovery | Timeout | Tracking During Failure | Connectivity During Failure |
|---|---:|---:|---:|---:|---:|
| `no_graph` | `30.0%` | `30.0%` | `70.0%` | `18.6%` | `12.9%` |
| `single` | `26.7%` | `26.7%` | `70.0%` | `39.4%` | `17.9%` |
| `multi_relation` | `86.7%` | `86.7%` | `13.3%` | `88.6%` | `32.7%` |

Seed-aware statistics:

- `multi_relation - single`: recovery delta `+60.0 pp`, 95% CI `[+20.0, +93.3] pp`;
- `multi_relation - no_graph`: recovery delta `+56.7 pp`, 95% CI `[-6.7, +100.0] pp`.

## Interpretation

The new communication-feasible semantics do not collapse the existing method ordering. In fact, the stricter information path increases separation between `multi_relation` and `single` in this small diagnostic.

The `no_graph` comparison remains noisy because seed 1 is much stronger than seeds 0 and 2. This reinforces the existing source-policy concern: a paper-facing run should either retrain all `no_graph` sources under one fixed policy or transparently report weak-source variance.

## Decision

Proceed to a small post-Gate-1 retraining diagnostic before any five-seed formal run.

Recommended next diagnostic:

- train `single` and `multi_relation` under the new communication-feasible semantics;
- use the frozen dropout-relay bottleneck protocol;
- start with seeds `0, 1, 2`;
- keep the budget small enough for iteration, then decide whether to launch formal five-seed training.

Do not use this checkpoint-reuse diagnostic as a final table.
