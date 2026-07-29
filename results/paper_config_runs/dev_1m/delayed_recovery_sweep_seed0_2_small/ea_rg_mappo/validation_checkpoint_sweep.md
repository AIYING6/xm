# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-29T05:18:27

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
scenarios = ['dropout030_delay2_relay_failure']
episodes = 5
base_seed = 270000
checkpoint_updates = [1600, 2200, 3000, 3800, 3907]
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 20
min_target_confidence = 0.2
multi_relation_global_residual_weight = 1.0
selection_metric = delayed_recovery
delayed_recovery_min_step = 80
selection_success_weight = 0.0
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Metric | Recovery | Delayed recovery | Recovery steps | Delayed steps | Success | Checkpoint |
| --- | --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_delay2_relay_failure | multi_relation | 0 | 3907 | delayed_recovery | 0 | 0 | inf | inf | 0 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_3907.pt` |
| dropout030_delay2_relay_failure | multi_relation | 1 | 3800 | delayed_recovery | 0.2 | 0.2 | 171 | 211 | 0.2 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_3800.pt` |
| dropout030_delay2_relay_failure | multi_relation | 2 | 3907 | delayed_recovery | 0 | 0 | inf | inf | 0 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_3907.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/delayed_recovery_sweep_seed0_2_small/ea_rg_mappo/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/delayed_recovery_sweep_seed0_2_small/ea_rg_mappo/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/delayed_recovery_sweep_seed0_2_small/ea_rg_mappo/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 15