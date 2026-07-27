# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-27T00:09:58

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0]
graph_encoders = ['no_graph']
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
| relay_failure | no_graph | 0 | 3800 | 0.62 | 17.8065 | 0.62 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3800.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/mappo_seed0/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/mappo_seed0/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/checkpoint_sweeps/mappo_seed0/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 47