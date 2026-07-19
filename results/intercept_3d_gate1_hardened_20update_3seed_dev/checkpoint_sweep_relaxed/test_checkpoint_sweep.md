# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T00:14:04

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
episodes = 50
base_seed = 230000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 20 | 0.58 | 5.31034 | 0.58 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.84 | 5.61905 | 0.84 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 20 | 0.96 | 5.39583 | 0.96 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 0 | 10 | 0.02 | 4 | 0.02 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed0/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 1 | 10 | 0.74 | 5.18919 | 0.74 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 2 | 20 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed2/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 0 | 20 | 0.78 | 5.4359 | 0.78 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 1 | 20 | 0.02 | 7 | 0.02 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 2 | 20 | 0.6 | 5.66667 | 0.6 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed2/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9