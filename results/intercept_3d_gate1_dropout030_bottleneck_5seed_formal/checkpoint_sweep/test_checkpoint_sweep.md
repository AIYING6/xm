# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T20:41:32

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [4]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 100
base_seed = 760000
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 40 | 0.98 | 6.07143 | 0.98 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0040.pt` |
| dropout030_relay_failure | multi_relation | 1 | 20 | 0.95 | 5.88421 | 0.95 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.46 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 10 | 0.92 | 54.587 | 0.92 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 4 | 20 | 0.96 | 8.55208 | 0.96 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 1 | 60 | 0.86 | 5.46512 | 0.86 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0.07 | 6.57143 | 0.07 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 3 | 10 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 4 | 50 | 0.78 | 5.5 | 0.78 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed4/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 0 | 30 | 0.77 | 5.75325 | 0.77 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0.3 | 6.33333 | 0.3 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 50 | 0.02 | 7 | 0.02 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 3 | 30 | 0.57 | 14.9649 | 0.57 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed3/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 4 | 10 | 0.93 | 5.63441 | 0.93 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed4/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 15