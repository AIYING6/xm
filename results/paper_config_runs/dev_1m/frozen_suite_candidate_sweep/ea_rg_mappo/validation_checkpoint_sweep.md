# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-29T12:34:51

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
graph_encoders = ['multi_relation']
scenarios = ['dropout030_delay2_relay_failure_early', 'dropout030_delay2_relay_failure', 'dropout030_delay2_relay_failure_delayed', 'dropout030_delay2_relay_failure_late']
episodes = 5
base_seed = 290000
checkpoint_updates = [1700, 2200, 3200, 3800, 3907]
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
multi_relation_global_residual_weight = 1.0
selection_metric = legacy_recovery
selection_group = suite
delayed_recovery_min_step = 80
selection_success_weight = 100.0
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Metric | Recovery | Delayed recovery | Recovery steps | Delayed steps | Success | Checkpoint |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| scenario_suite | multi_relation | 0 | 1700 | legacy_recovery | 0.6 | 0 | inf | inf | 0.8 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_1700.pt` |
| scenario_suite | multi_relation | 1 | 3800 | legacy_recovery | 0.25 | 0.25 | inf | inf | 0.25 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_3800.pt` |
| scenario_suite | multi_relation | 2 | 3200 | legacy_recovery | 0.15 | 0 | inf | inf | 0.25 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_3200.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/frozen_suite_candidate_sweep/ea_rg_mappo/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/frozen_suite_candidate_sweep/ea_rg_mappo/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/frozen_suite_candidate_sweep/ea_rg_mappo/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 60