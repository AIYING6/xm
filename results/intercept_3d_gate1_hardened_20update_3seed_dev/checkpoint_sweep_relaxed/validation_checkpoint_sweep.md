# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T00:06:05

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
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 30
base_seed = 220000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 20 | 0.466667 | 5.21429 | 0.466667 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.933333 | 5.92857 | 0.933333 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 20 | 1 | 5.63333 | 1 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0020.pt` |
| dropout030_relay_failure | no_graph | 0 | 10 | 0.0333333 | 4 | 0.0333333 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed0/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 1 | 10 | 0.633333 | 5.36842 | 0.633333 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 2 | 20 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/no_graph/bc_ppo_seed2/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 0 | 20 | 0.733333 | 5.63636 | 0.733333 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 1 | 20 | 0.133333 | 6.5 | 0.133333 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 2 | 20 | 0.7 | 5.80952 | 0.7 | `results/intercept_3d_gate1_hardened_20update_3seed_dev/runs/single/bc_ppo_seed2/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_hardened_20update_3seed_dev/checkpoint_sweep_relaxed/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 18