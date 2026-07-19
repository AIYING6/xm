# No-Role-Pair-Gate Ablation, Hardened Safety Fixed-Update-60

Last updated: 2026-07-19

## Status

This is the second five-seed hardened safety ablation under the frozen fixed `update_0060` protocol.

The ablation removes role-pair-conditioned message gating while keeping the `multi_relation` graph encoder, all relation channels, strict target sensing, target-information bottleneck, TTL/confidence target-cache validity, post-step timing, and the same light proximity safety auxiliary.

Unlike the `no_task_support` ablation, this result gives a cleaner seed-aware separation from the full method.

## Protocol

- Ablation root: `results/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate/`
- Main comparison root: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/`
- Graph encoder: `multi_relation`
- Ablation: `graph_message_ablation=no_role_pair_gate`
- Seeds: `0, 1, 2, 3, 4`
- Training: `60` safety-continuation PPO updates from the same five source checkpoints used by the full method
- Test split: `dropout030_relay_failure`, `100` episodes per seed
- Matched evaluation base seed: `310000`
- Fixed checkpoint: `actor_critic_update_0060.pt`
- Safety auxiliary: `safety_proximity_distance=1000`, `safety_proximity_penalty_weight=0.3`

## Test Results

Values are seed-level mean plus sample standard deviation across five training seeds.

| Method | Recovery / success | Tracking during failure | Connectivity during failure | Chain closed during failure | Timeout | Collision | Min blue-red distance | Min blue-blue distance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Full `multi_relation` | 0.886 +/- 0.137 | 0.776 +/- 0.168 | 0.203 +/- 0.018 | 0.138 +/- 0.029 | 0.114 +/- 0.137 | 0.000 +/- 0.000 | 3276.94 m | 2011.36 m |
| `no_role_pair_gate` | 0.648 +/- 0.380 | 0.607 +/- 0.380 | 0.165 +/- 0.075 | 0.099 +/- 0.064 | 0.352 +/- 0.380 | 0.000 +/- 0.000 | 3116.78 m | 2047.52 m |

Seed-level recovery:

- Full `multi_relation`: `[0.65, 0.90, 0.99, 0.92, 0.97]`
- `no_role_pair_gate`: `[0.53, 0.85, 1.00, 0.82, 0.04]`

## Seed-Aware Comparison

Hierarchical bootstrap first resamples training seeds and then matched episodes inside each seed.

Full `multi_relation` versus `no_role_pair_gate`:

- Recovery / success delta: `+0.238`, 95% CI `[+0.028, +0.592]`
- Timeout delta: `-0.238`, 95% CI `[-0.592, -0.028]`
- Restricted mean recovery steps delta: `-51.718`, 95% CI `[-129.837, -5.774]`
- Tracking during failure delta: `+0.169`, 95% CI `[+0.027, +0.388]`
- Connectivity during failure delta: `+0.038`, 95% CI `[-0.003, +0.109]`
- Chain closure during failure delta: `+0.039`, 95% CI `[+0.002, +0.102]`

## Interpretation

This is the stronger of the two current mechanism ablations:

- Removing role-pair message gating lowers average recovery from `88.6%` to `64.8%`.
- The recovery, timeout, restricted recovery time, tracking, and chain-closure intervals all separate in favor of the full method.
- Both full and ablated methods have zero collisions, so the difference is not driven by safety failures.
- Seed `2` is the only seed where the ablation slightly beats the full method; seed `4` shows the largest collapse.

Paper use:

- Safe statement: role-pair-conditioned message gating improves post-failure recovery probability, reduces timeout, and improves failure-window tracking/chain closure under the fixed-budget hardened safety protocol.
- Avoid statement: role-pair gating is the only necessary mechanism; task-support relation evidence is supportive but less statistically clean.

## Artifacts

- Ablation test summary: `results/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate/checkpoint_sweep_fixed_update60_test_matched_full/test_checkpoint_summary.csv`
- Ablation episode metrics: `results/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate/checkpoint_sweep_fixed_update60_test_matched_full/test_episode_metrics.csv`
- Matched comparison CSV: `results/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate/comparison_vs_full/combined_episode_metrics_full_vs_no_role_pair_gate_matched_full.csv`
- Seed-aware statistics: `results/intercept_3d_gate1_hardened_safety_no_role_pair_gate_5seed_fixed_update60_candidate/comparison_vs_full/seed_aware_stats_matched_full/intercept_3d_strict_sensing_seed_aware_bootstrap.csv`

## Follow-Up

1. Promote `no_role_pair_gate` as the primary mechanism ablation.
2. Keep `no_task_support` as a secondary/supportive ablation because its confidence interval crosses zero.
3. Decide whether `no_curriculum` is still worth running. It is useful for training-method claims, but less central than the now-completed role/message ablations.
