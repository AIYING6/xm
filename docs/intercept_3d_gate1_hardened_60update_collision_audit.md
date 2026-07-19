# Hardened 60-Update Collision Audit

Last updated: 2026-07-18

## Scope

This audit inspects disjoint-test collision episodes from:

```text
results/intercept_3d_gate1_hardened_60update_3seed_dev/checkpoint_sweep/test_episode_metrics.csv
```

The validation-selected checkpoints all satisfied the zero-collision validation gate, but the independent test split still contained three collision episodes.

## Collision Episodes

| Method | Train seed | Checkpoint update | Episode seed | Episode | Success | Recovered | Steps | Timeout | Final mean range |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `multi_relation` | 1 | 20 | 250019 | 19 | 0 | 0 | 45 | 0 | 5757.3 |
| `single` | 1 | 30 | 250009 | 9 | 0 | 0 | 55 | 0 | 3100.9 |
| `single` | 1 | 30 | 250025 | 25 | 0 | 0 | 55 | 0 | 3640.5 |

Aggregate collision rates:

- `no_graph`: `0.000`;
- `single`: `0.013` mean across three training seeds;
- `multi_relation`: `0.007` mean across three training seeds.

## Interpretation

The collision issue is small in count but important for paper quality:

- the strict validation gate did not guarantee zero collision on the disjoint test split;
- both affected methods involve train seed `1`, so this may be a seed-specific policy stability issue;
- `single` has both lower recovery and more collision in seed `1`;
- `multi_relation` has one collision while otherwise maintaining strong recovery.

This does not invalidate the method-ordering result, but it blocks a clean final claim until safety handling is clarified.

## Metric Semantics Note

Some collision rows show `post_failure_chain_recovered=0` but a finite `post_failure_chain_recovery_steps` value. This is expected under the current evaluator semantics:

- if recovery occurs, the value is the first post-failure chain-closure step minus failure-start step;
- if recovery does not occur, the value is a censored duration from failure start to episode end.

For manuscript tables, recovery probability and restricted mean recovery time should be reported separately. The raw `post_failure_chain_recovery_steps` column should not be described as a recovered-only mean.

## Recommended Next Fix

Before formal five-seed training:

1. Replay the three collision episodes with per-step minimum blue-blue distance, chain-closure state, tracking state, and active failure state.
2. Decide whether to add a small collision/safety penalty or action-smoothing regularizer before final training.

## Follow-Up Completed

`scripts/evaluate_ri_gmappo_3d.py` now keeps the legacy `post_failure_chain_recovery_steps` field for compatibility and adds:

- `post_failure_chain_recovery_steps_censored`;
- `post_failure_chain_recovered_only_steps`.

A one-episode evaluator smoke under `results/intercept_3d_gate1_hardened_60update_3seed_dev/field_semantics_smoke/` confirmed that both new columns are written.

`scripts/replay_3d_collision_cases.py` now replays collision episodes and writes per-step distance/action traces.

Replay outputs:

- `results/intercept_3d_gate1_hardened_60update_3seed_dev/collision_replay/collision_replay_trace.csv`;
- `docs/intercept_3d_gate1_hardened_60update_collision_replay.md`.

Replay findings:

- `multi_relation` has one blue-blue collision: `blue0-blue2` at step `45`, minimum blue-blue distance `114.2 m`;
- `single` has two blue-target collisions: `blue0-red0` at steps `55`, minimum blue-red distances `31.3 m` and `103.0 m`;
- all three collisions occur during the configured relay-failure interval;
- distance traces show sustained unsafe approach before termination, so this is better treated as a safety-shaping/evaluation issue than as random numerical noise.

Current decision:

- do not launch the five-seed formal rerun yet;
- first run a light safety-policy diagnostic, preferably with a small collision-proximity penalty or action smoothing, and verify that recovery remains high while test collision decreases.
