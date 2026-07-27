# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-27T01:03:31

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
scenarios = ['relay_failure']
episodes = 100
base_seed = 220000
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/paper_config_runs/dev_1m/checkpoint_sweeps/seed0_graph_validation_selected_checkpoints.csv
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 0 | 1600 | 0.89 | 18.9663 | 0.89 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_1600.pt` |
| relay_failure | no_graph | 0 | 3800 | 0.6 | 17.8667 | 0.6 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3800.pt` |
| relay_failure | single | 0 | 3907 | 0.8 | 19.4875 | 0.8 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_3907.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/test_eval/seed0_graph_selected/test_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/test_eval/seed0_graph_selected/test_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/test_eval/seed0_graph_selected/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 3