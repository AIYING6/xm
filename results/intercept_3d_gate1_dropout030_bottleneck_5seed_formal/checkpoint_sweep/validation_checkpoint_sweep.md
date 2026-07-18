# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T20:20:09

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [4]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 750000
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = none
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 40 | 1 | 6.44 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0040.pt` |
| dropout030_relay_failure | multi_relation | 1 | 20 | 0.98 | 6.38776 | 0.98 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.86 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 10 | 0.98 | 38.6735 | 0.98 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 4 | 20 | 0.96 | 12.3125 | 0.96 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 1 | 60 | 0.94 | 5.74468 | 0.94 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0.1 | 6.4 | 0.1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 3 | 10 | 0.02 | 5 | 0.02 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 4 | 50 | 0.88 | 5.84091 | 0.88 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed4/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 0 | 30 | 0.62 | 6.25806 | 0.62 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0.36 | 6.5 | 0.36 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 50 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 3 | 30 | 0.7 | 17.8857 | 0.7 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed3/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 4 | 10 | 0.98 | 6.02041 | 0.98 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed4/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 90