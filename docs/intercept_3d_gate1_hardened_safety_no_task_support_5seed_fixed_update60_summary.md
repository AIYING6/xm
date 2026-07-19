# No-Task-Support Ablation, Hardened Safety Fixed-Update-60

Last updated: 2026-07-19

## Status

This is the first five-seed hardened safety ablation under the fixed `update_0060` protocol.

The ablation removes the task-support relation while keeping the `multi_relation` graph encoder, strict target sensing, target-information bottleneck, TTL/confidence target-cache validity, post-step timing, and the same light proximity safety auxiliary.

This result is useful as a mechanism ablation, but it should be written conservatively because the seed-aware confidence interval versus the full method still crosses zero.

## Protocol

- Ablation root: `results/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate/`
- Main comparison root: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/`
- Graph encoder: `multi_relation`
- Ablation: `graph_relation_ablation=no_task_support`
- Seeds: `0, 1, 2, 3, 4`
- Training: `60` safety-continuation PPO updates from the same five source checkpoints used by the full method
- Test split: `dropout030_relay_failure`, `100` episodes per seed
- Matched evaluation base seed: `310000`
- Fixed checkpoint: `actor_critic_update_0060.pt`
- Safety auxiliary: `safety_proximity_distance=1000`, `safety_proximity_penalty_weight=0.3`

An earlier `base_seed=130000` test was run during setup and is not used for the matched comparison.

## Test Results

Values are seed-level mean plus sample standard deviation across five training seeds.

| Method | Recovery / success | Tracking during failure | Connectivity during failure | Chain closed during failure | Timeout | Collision | Min blue-red distance | Min blue-blue distance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full `multi_relation` | 0.886 +/- 0.137 | 0.776 +/- 0.168 | 0.203 +/- 0.018 | 0.138 +/- 0.029 | 0.114 +/- 0.137 | 0.000 +/- 0.000 | 3276.94 m | 2011.36 m |
| `no_task_support` | 0.648 +/- 0.373 | 0.596 +/- 0.394 | 0.160 +/- 0.078 | 0.089 +/- 0.063 | 0.344 +/- 0.376 | 0.008 +/- 0.008 | 3137.91 m | 2044.43 m |

Seed-level recovery:

- Full `multi_relation`: `[0.65, 0.90, 0.99, 0.92, 0.97]`
- `no_task_support`: `[0.91, 0.89, 0.72, 0.72, 0.00]`

## Seed-Aware Comparison

Hierarchical bootstrap first resamples training seeds and then matched episodes inside each seed.

Full `multi_relation` versus `no_task_support`:

- Recovery / success delta: `+0.238`, 95% CI `[-0.092, +0.636]`
- Timeout delta: `-0.230`, 95% CI `[-0.632, +0.098]`
- Restricted mean recovery steps delta: `-52.162`, 95% CI `[-137.263, +19.056]`
- Tracking during failure delta: `+0.180`, 95% CI `[-0.063, +0.423]`
- Connectivity during failure delta: `+0.042`, 95% CI `[-0.010, +0.113]`
- Chain closure during failure delta: `+0.048`, 95% CI `[-0.009, +0.110]`

## Interpretation

The ablation supports the direction of the task-support mechanism but is not yet a clean significance result:

- Mean recovery drops from `88.6%` to `64.8%` when task-support relations are removed.
- The full method has zero collisions, while `no_task_support` has `0.8%` mean collision rate.
- Full `multi_relation` is better on seeds `2`, `3`, and `4`, roughly tied on seed `1`, and worse on seed `0`.
- The main uncertainty comes from seed-level heterogeneity: `no_task_support` seed `4` fails completely, while seed `0` is stronger than the full method.

Paper use:

- Safe statement: task-support relations improve the average recovery level and reduce failure cases in this fixed-budget setting.
- Avoid statement: task-support relations are statistically decisive across all seeds.

## Artifacts

- Ablation test summary: `results/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate/checkpoint_sweep_fixed_update60_test_matched_full/test_checkpoint_summary.csv`
- Ablation episode metrics: `results/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate/checkpoint_sweep_fixed_update60_test_matched_full/test_episode_metrics.csv`
- Matched comparison CSV: `results/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate/comparison_vs_full/combined_episode_metrics_full_vs_no_task_support_matched_full.csv`
- Seed-aware statistics: `results/intercept_3d_gate1_hardened_safety_no_task_support_5seed_fixed_update60_candidate/comparison_vs_full/seed_aware_stats_matched_full/intercept_3d_strict_sensing_seed_aware_bootstrap.csv`

## Follow-Up

1. Run the `no_role_pair_gate` ablation under the same frozen fixed-update-60 safety protocol.
2. Inspect seed `4` for `no_task_support` to determine whether it is a plausible task-support failure mode or a training instability outlier.
3. If both ablations are mixed, do not overemphasize individual ablations; instead report them as mechanism diagnostics and rely on the stronger `single` / `no_graph` baselines for the main claim.
