# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-28T04:07:38

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
episodes = 50
base_seed = 130000
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
| dropout030_relay_failure | multi_relation | 0 | 1500 | 0.2 | 17.5 | 0.2 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_1500.pt` |
| dropout030_relay_failure | multi_relation | 1 | 3800 | 0.4 | 163.7 | 0.4 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_3800.pt` |
| dropout030_relay_failure | multi_relation | 2 | 2400 | 0.42 | 27.2857 | 0.42 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_2400.pt` |
| dropout030_relay_failure | no_graph | 0 | 3600 | 0.52 | 17.5385 | 0.52 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3600.pt` |
| dropout030_relay_failure | no_graph | 1 | 2300 | 0.9 | 22.9111 | 0.9 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1/actor_critic_update_2300.pt` |
| dropout030_relay_failure | no_graph | 2 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed2/actor_critic_update_3907.pt` |
| dropout030_relay_failure | single | 0 | 1800 | 0.5 | 10 | 0.5 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_1800.pt` |
| dropout030_relay_failure | single | 1 | 200 | 0.16 | 20.75 | 0.16 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0200.pt` |
| dropout030_relay_failure | single | 2 | 2560 | 0.58 | 22.1034 | 0.58 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_2560.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_relay_failure_seed0_2_validation/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_relay_failure_seed0_2_validation/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/checkpoint_sweeps/dropout030_relay_failure_seed0_2_validation/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 443