# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T15:14:32

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
base_seed = 886001
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = results/intercept_3d_gate1_post_change_retrain_20update_diag/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 5 | 0.85 | 5.94118 | 0.85 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0005.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.95 | 5.89474 | 0.95 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 15 | 1 | 5.7 | 1 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0015.pt` |
| dropout030_relay_failure | single | 0 | 20 | 0.7 | 5.92857 | 0.7 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 1 | 5 | 0.2 | 6.5 | 0.2 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0005.pt` |
| dropout030_relay_failure | single | 2 | 5 | 0.1 | 6 | 0.1 | `results/intercept_3d_gate1_post_change_retrain_20update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0005.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_post_change_retrain_20update_diag/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_post_change_retrain_20update_diag/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_post_change_retrain_20update_diag/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6