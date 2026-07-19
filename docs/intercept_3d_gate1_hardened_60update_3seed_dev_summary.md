# Hardened Gate 1 60-Update Three-Seed Development Summary

Last updated: 2026-07-18

## Purpose

This run follows the 20-update hardened development diagnostic and checks whether a longer budget can pass strict zero-collision validation checkpoint selection under:

```text
dropout030_relay_failure + strict_target_sensing + agent_target_info_bottleneck
```

This is still a development result, not final paper evidence. Its role is to decide whether the hardened Gate 1 line is strong enough to move toward a five-seed formal rerun.

## Protocol

Output directory:

```text
results/intercept_3d_gate1_hardened_60update_3seed_dev/
```

Training/evaluation setup:

- methods: `no_graph`, `single`, `multi_relation`;
- seeds: `0, 1, 2`;
- PPO updates: `60`;
- checkpoint snapshots: every `10` updates;
- validation: 30 matched episodes, base seed `240000`;
- test: 50 matched episodes, base seed `250000`;
- strict target sensing: enabled;
- agent target-information bottleneck: enabled;
- target-message freshness: `max_target_message_age_steps=80`, `min_target_confidence=0.2`;
- checkpoint selection safety gate: `max_selection_collision_rate=0.0` on validation.

## Validation Selection

The strict zero-collision validation gate passed.

Selected checkpoints:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | update 20 | update 30 | update 60 |
| `single` | update 60 | update 30 | update 60 |
| `multi_relation` | update 60 | update 20 | update 10 |

Validation recovery:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | 0.033 | 0.733 | 0.000 |
| `single` | 1.000 | 0.100 | 0.800 |
| `multi_relation` | 0.833 | 0.867 | 1.000 |

Important point: the `single` method can solve some seeds very well but still has a severe weak-seed failure mode. The `multi_relation` method is less saturated than the best `single` seed but much more stable across seeds.

## Disjoint Test Result

Test result over 50 episodes per seed:

| Method | Recovery / Success | Tracking During Failure | Connectivity During Failure | Timeout | Collision |
|---|---:|---:|---:|---:|---:|
| `no_graph` | 0.267 +/- 0.411 | 0.161 +/- 0.252 | 0.089 +/- 0.077 | 0.733 +/- 0.411 | 0.000 +/- 0.000 |
| `single` | 0.613 +/- 0.473 | 0.669 +/- 0.405 | 0.170 +/- 0.068 | 0.373 +/- 0.450 | 0.013 +/- 0.023 |
| `multi_relation` | 0.853 +/- 0.070 | 0.870 +/- 0.068 | 0.213 +/- 0.017 | 0.140 +/- 0.072 | 0.007 +/- 0.012 |

Seed-level test recovery:

| Method | Seed 0 | Seed 1 | Seed 2 |
|---|---:|---:|---:|
| `no_graph` | 0.060 | 0.740 | 0.000 |
| `single` | 0.980 | 0.080 | 0.780 |
| `multi_relation` | 0.780 | 0.860 | 0.920 |

## Interpretation

The 60-update result is stronger than the 20-update diagnostic:

- strict validation checkpoint selection passed for all method/seed pairs;
- `multi_relation` has the highest mean recovery and the lowest seed variance;
- `single` remains unstable because seed 1 collapses despite the longer budget;
- `no_graph` remains weak and highly seed-dependent;
- `multi_relation` improves failure-time tracking and connectivity, matching the intended mechanism.

However, the result is not yet formal paper evidence:

- validation selection enforced zero collision, but disjoint test still produced nonzero collision for `multi_relation` seed 1 (`0.02`) and `single` seed 1 (`0.04`);
- only three training seeds are used;
- seed-aware statistics separate `multi_relation` from `no_graph`, but not yet from `single`;
- no failure-aligned mechanism curve has been regenerated for the hardened result.

Seed-aware hierarchical bootstrap reports were generated after this summary:

- `docs/intercept_3d_gate1_hardened_60update_seed_aware_multi_vs_single/intercept_3d_strict_sensing_seed_aware_bootstrap.md`;
- `docs/intercept_3d_gate1_hardened_60update_seed_aware_multi_vs_no_graph/intercept_3d_strict_sensing_seed_aware_bootstrap.md`.

Key intervals:

- `multi_relation - no_graph`: recovery `+58.7 pp`, 95% CI `[+14.7, +90.7] pp`;
- `multi_relation - single`: recovery `+24.0 pp`, 95% CI `[-18.0, +76.7] pp`.

Collision details are recorded in `docs/intercept_3d_gate1_hardened_60update_collision_audit.md`.

## Decision

This run supports continuing the current Q1 route. The next step should not be 5v2, JSBSim, missile simulation, or self-play.

Recommended next step:

1. Replay the three collision episodes with per-step minimum-distance and chain-state traces.
2. Add a hardened failure-aligned mechanism analysis for `multi_relation` versus `single`.
3. Decide whether to add a small safety penalty or action smoothing before any five-seed formal rerun.
4. If safety is acceptable after inspection, freeze the protocol and run a five-seed formal hardened rerun with larger test episodes.

Completed follow-up:

- `scripts/evaluate_ri_gmappo_3d.py` now writes explicit censored and recovered-only recovery-time fields for future evaluator outputs.

Current conclusion:

```text
multi_relation is the strongest and most stable method under the hardened dropout-relay bottleneck protocol,
but safety/collision evidence must be cleaned up before final paper-level claims.
```
