# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-27T16:02:51

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [1, 2]
graph_encoders = ['single']
scenarios = ['relay_failure']
episodes = 50
base_seed = 120000
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | single | 1 | 40 | 0.04 | 78.5 | 0.04 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0040.pt` |
| relay_failure | single | 2 | 40 | 0.44 | 23.4545 | 0.44 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_0040.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/single_graph_seeds1_2/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/single_graph_seeds1_2/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/checkpoint_sweeps/single_graph_seeds1_2/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 100