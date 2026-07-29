# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-29T17:53:14

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Default selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
When selection_metric=delayed_recovery, recovery_rate and recovery_steps use delayed recovery.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2]
graph_encoders = ['single']
scenarios = ['dropout030_delay2_relay_failure_early', 'dropout030_delay2_relay_failure', 'dropout030_delay2_relay_failure_delayed', 'dropout030_delay2_relay_failure_late']
episodes = 10
base_seed = 291000
checkpoint_updates = [20, 30, 40]
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
multi_relation_global_residual_weight = 1.0
selection_metric = delayed_recovery
selection_group = suite
delayed_recovery_min_step = 80
selection_success_weight = 0.0
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Metric | Recovery | Delayed recovery | Recovery steps | Delayed steps | Success | Checkpoint |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| scenario_suite | single | 0 | 20 | delayed_recovery | 0.75 | 0.4 | 58.933 | 189.464 | 0.725 | `results/paper_config_runs/stability_dev/single_graph_seed0_strong_offset_balanced_recovery_bc_safety05_ppo_h64/actor_critic_update_0020.pt` |
| scenario_suite | single | 1 | 20 | delayed_recovery | 0.725 | 0.275 | 93.6472 | inf | 0.55 | `results/paper_config_runs/stability_dev/single_graph_seed1_strong_offset_balanced_recovery_bc_safety05_ppo_h64/actor_critic_update_0020.pt` |
| scenario_suite | single | 2 | 20 | delayed_recovery | 0.875 | 0.4 | 54.1431 | inf | 0.75 | `results/paper_config_runs/stability_dev/single_graph_seed2_strong_offset_balanced_recovery_bc_safety05_ppo_h64/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/stability_dev/checkpoint_sweeps/single_graph_strong_offset_balanced_recovery_bc_safety05_seed0_2_dev40/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/stability_dev/checkpoint_sweeps/single_graph_strong_offset_balanced_recovery_bc_safety05_seed0_2_dev40/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/stability_dev/checkpoint_sweeps/single_graph_strong_offset_balanced_recovery_bc_safety05_seed0_2_dev40/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 36