# Hardened Gate 1 20-Update Three-Seed Development Summary

Last updated: 2026-07-18

## Purpose

This run checks whether the `dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck` result still holds after the Gate 1 P0 hardening changes:

- decentralized actor observation localization;
- target-message TTL and confidence filtering;
- post-step failure/message timing semantics;
- strict-bottleneck graph target node hiding when no agent currently detects the target.

The run is a development rerun only. It must not be treated as final paper evidence because the strict zero-collision checkpoint-selection gate failed for one baseline seed.

## Protocol

Output directory:

```text
results/intercept_3d_gate1_hardened_20update_3seed_dev/
```

Training setup:

- scenario: `dropout030_relay_failure`;
- methods: `no_graph`, `single`, `multi_relation`;
- training seeds: `0, 1, 2`;
- PPO budget: 20 updates;
- checkpoint snapshots: every 10 updates;
- validation: 30 matched episodes, base seed `220000`;
- test: 50 matched episodes, base seed `230000`;
- strict sensing: enabled;
- agent target-information bottleneck: enabled;
- target-message freshness: `max_target_message_age_steps=80`, `min_target_confidence=0.2`;
- device: CPU.

## Strict Gate Outcome

The strict validation command used `--max-selection-collision-rate 0.0`.

Training and validation evaluation completed, but strict checkpoint selection failed:

```text
no collision-eligible checkpoint for split=validation,
scenario=dropout030_relay_failure,
graph_encoder=single,
train_seed=1
```

Reason: both available `single` seed-1 validation candidates had nonzero collision rate (`0.0333333`). This is a real safety/protocol issue, not a code crash.

Interpretation:

- the hardened code path is executable;
- the current zero-collision gate is too strict for this short 20-update development budget;
- formal evidence should either train until all methods satisfy the predefined safety gate, or use a predefined nonzero safety threshold and report collision explicitly.

## Relaxed Diagnostic Result

A relaxed selection diagnostic was run to understand method ordering. This diagnostic did not use the zero-collision gate and is not final paper evidence.

Selected validation checkpoints:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | update 10 | update 10 | update 20 |
| `single` | update 20 | update 20 | update 20 |
| `multi_relation` | update 20 | update 10 | update 20 |

Disjoint test result over 50 episodes per seed:

| Method | Recovery / Success | Tracking During Failure | Connectivity During Failure | Timeout | Collision |
|---|---:|---:|---:|---:|---:|
| `no_graph` | 0.253 +/- 0.422 | 0.151 +/- 0.244 | 0.090 +/- 0.080 | 0.740 +/- 0.416 | 0.007 +/- 0.012 |
| `single` | 0.467 +/- 0.397 | 0.546 +/- 0.341 | 0.165 +/- 0.074 | 0.527 +/- 0.386 | 0.007 +/- 0.012 |
| `multi_relation` | 0.793 +/- 0.194 | 0.820 +/- 0.165 | 0.213 +/- 0.026 | 0.207 +/- 0.194 | 0.000 +/- 0.000 |

Seed-level recovery:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | 0.020 | 0.740 | 0.000 |
| `single` | 0.780 | 0.020 | 0.600 |
| `multi_relation` | 0.580 | 0.840 | 0.960 |

## Decision

The diagnostic preserves the expected ordering:

```text
no_graph < single < multi_relation
```

The most important observation is stability, not only the mean:

- `multi_relation` is the only method with all three seeds above 0.50 recovery and zero test collisions;
- `single` has one near-failed seed and one strict-validation safety failure;
- `no_graph` has two near-failed seeds.

This supports continuing the Q1 route centered on multi-relation task-chain recovery, but it is still not enough to start final five-seed formal experiments.

## Next Action

Do not launch final five-seed ablations yet.

Recommended next step:

1. Add a predefined 60-update hardened development rerun for all three methods under the same dropout-relay bottleneck protocol.
2. Keep validation/test splits fixed and disjoint.
3. Use a safety policy before launch:
   - primary option: keep `max_selection_collision_rate=0.0`, but increase training budget so all methods have a chance to satisfy it;
   - fallback option for development only: allow `max_selection_collision_rate=0.02` or `0.05`, while reporting collision in the main table and labeling the result diagnostic.
4. If `single` still has nonzero collision or unstable seeds at 60 updates, inspect reward/safety terms before scaling to five seeds.
5. Only promote to formal evidence after the three-method development rerun satisfies the predefined selection protocol.

