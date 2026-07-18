# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T12:57:06

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0, 1, 2]
graph_encoders = ['single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 740000
strict_target_sensing = True
selection_csv = results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 30 | 1 | 6.7 | 1 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.85 | 5.94118 | 0.85 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 30 | 1 | 5.8 | 1 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.7 | 5.28571 | 0.7 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 30 | 0.7 | 5.35714 | 0.7 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 2 | 50 | 0.95 | 5.42105 | 0.95 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed2/actor_critic_update_0050.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_fair_60update_dropout030_info_bottleneck_probe/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_fair_60update_dropout030_info_bottleneck_probe/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_fair_60update_dropout030_info_bottleneck_probe/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6