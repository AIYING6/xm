# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T15:29:00

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2]
graph_encoders = ['single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 10
base_seed = 887001
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = none
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 40 | 1 | 5.9 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0040.pt` |
| dropout030_relay_failure | multi_relation | 1 | 20 | 1 | 5.6 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.3 | 1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.9 | 5.44444 | 0.9 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0.3 | 7 | 0.3 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 10 | 0.1 | 7 | 0.1 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_post_change_retrain_60update_diag/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_post_change_retrain_60update_diag/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_post_change_retrain_60update_diag/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 36