# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T15:53:25

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
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 891001
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = results/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 40 | 1 | 5.9 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0040.pt` |
| dropout030_relay_failure | multi_relation | 1 | 40 | 0.95 | 5.94737 | 0.95 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0040.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.4 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 1 | 20 | 0.95 | 5.42105 | 0.95 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.75 | 5.8 | 0.75 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 50 | 0.25 | 6.6 | 0.25 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 2 | 10 | 0.15 | 6.66667 | 0.15 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_post_change_retrain_60update_three_method_safety_selected_diag/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9