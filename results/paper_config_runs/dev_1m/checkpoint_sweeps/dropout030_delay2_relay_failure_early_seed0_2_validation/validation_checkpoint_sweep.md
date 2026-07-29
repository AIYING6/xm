# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-29T00:06:05

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [2]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_delay2_relay_failure_early']
episodes = 50
base_seed = 140000
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
| dropout030_delay2_relay_failure_early | multi_relation | 0 | 100 | 0.28 | 26 | 0.28 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_0100.pt` |
| dropout030_delay2_relay_failure_early | multi_relation | 1 | 1200 | 0.72 | 38.2222 | 0.72 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_1200.pt` |
| dropout030_delay2_relay_failure_early | multi_relation | 2 | 2900 | 0.42 | 39.0476 | 0.42 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_2900.pt` |
| dropout030_delay2_relay_failure_early | no_graph | 0 | 3400 | 0.62 | 34.2258 | 0.62 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3400.pt` |
| dropout030_delay2_relay_failure_early | no_graph | 1 | 3060 | 0.48 | 70.0417 | 0.48 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1/actor_critic_update_3060.pt` |
| dropout030_delay2_relay_failure_early | no_graph | 2 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed2/actor_critic_update_3907.pt` |
| dropout030_delay2_relay_failure_early | single | 0 | 1800 | 0.6 | 25.2333 | 0.6 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_1800.pt` |
| dropout030_delay2_relay_failure_early | single | 1 | 200 | 0.32 | 35.8125 | 0.32 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0200.pt` |
| dropout030_delay2_relay_failure_early | single | 2 | 2560 | 0.66 | 38.303 | 0.66 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_2560.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_early_seed0_2_validation/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 443