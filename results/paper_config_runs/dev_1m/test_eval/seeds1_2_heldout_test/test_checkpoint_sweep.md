# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-27T22:34:05

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [1, 2]
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['relay_failure']
episodes = 100
base_seed = 220000
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/paper_config_runs/dev_1m/checkpoint_sweeps/seed1_2_validation_selected_for_test.csv
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 1 | 2200 | 0.37 | 34 | 0.37 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_2200.pt` |
| relay_failure | multi_relation | 2 | 3800 | 0.31 | 25.2258 | 0.31 | `results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_3800.pt` |
| relay_failure | no_graph | 1 | 2400 | 0.93 | 19.9462 | 0.93 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1/actor_critic_update_2400.pt` |
| relay_failure | no_graph | 2 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed2/actor_critic_update_3907.pt` |
| relay_failure | single | 1 | 40 | 0.03 | 77 | 0.03 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0040.pt` |
| relay_failure | single | 2 | 40 | 0.57 | 27.6842 | 0.57 | `results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_0040.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/dev_1m/test_eval/seeds1_2_heldout_test/test_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/dev_1m/test_eval/seeds1_2_heldout_test/test_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/dev_1m/test_eval/seeds1_2_heldout_test/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6