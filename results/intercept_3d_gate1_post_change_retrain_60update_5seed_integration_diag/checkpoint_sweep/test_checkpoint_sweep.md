# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T18:22:43

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0, 1, 2, 3, 4]
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 10
base_seed = 895001
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = results/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 60 | 0.8 | 5.375 | 0.8 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 1 | 5.5 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.2 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 60 | 0.9 | 56.1111 | 0.9 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 4 | 20 | 1 | 5.1 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 0 | 20 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 1 | 20 | 0.6 | 5.5 | 0.6 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 4 | 60 | 0.7 | 5.57143 | 0.7 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.8 | 5.25 | 0.8 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 50 | 0.3 | 5.66667 | 0.3 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 3 | 30 | 0.5 | 6 | 0.5 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed3/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 4 | 30 | 0.7 | 5 | 0.7 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed4/actor_critic_update_0030.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_post_change_retrain_60update_5seed_integration_diag/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 15