# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-28T10:09:45

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
scenarios = ['dropout030_delay2_relay_failure']
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
| dropout030_delay2_relay_failure | multi_relation | 0 | 1700 | 0.76 | 22.5526 | 0.76 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_1700.pt` |
| dropout030_delay2_relay_failure | multi_relation | 1 | 2200 | 0.42 | 49.3333 | 0.42 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_2200.pt` |
| dropout030_delay2_relay_failure | multi_relation | 2 | 2400 | 0.5 | 26.88 | 0.5 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_2400.pt` |
| dropout030_delay2_relay_failure | no_graph | 0 | 3400 | 0.64 | 19.4062 | 0.64 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3400.pt` |
| dropout030_delay2_relay_failure | no_graph | 1 | 2400 | 0.78 | 19 | 0.78 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1/actor_critic_update_2400.pt` |
| dropout030_delay2_relay_failure | no_graph | 2 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed2/actor_critic_update_3907.pt` |
| dropout030_delay2_relay_failure | single | 0 | 1800 | 0.56 | 9.89286 | 0.56 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_1800.pt` |
| dropout030_delay2_relay_failure | single | 1 | 200 | 0.32 | 20.8125 | 0.32 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0200.pt` |
| dropout030_delay2_relay_failure | single | 2 | 2560 | 0.8 | 23.1 | 0.8 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_2560.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_seed0_2_validation/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_seed0_2_validation/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_delay2_relay_failure_seed0_2_validation/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 443