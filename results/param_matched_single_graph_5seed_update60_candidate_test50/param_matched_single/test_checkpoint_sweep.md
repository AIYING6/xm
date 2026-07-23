# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T04:35:21

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0, 1, 2, 3, 4]
graph_encoders = ['single']
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 372000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/checkpoint_selection_all5/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | single | 0 | 20 | 0.64 | 38 | 0.64 | `results/param_matched_single_graph_3seed_bottleneck_strict_update60_dev/runs/single/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0 | inf | 0 | `results/param_matched_single_graph_3seed_bottleneck_strict_update60_dev/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 60 | 0 | inf | 0 | `results/param_matched_single_graph_3seed_bottleneck_strict_update60_dev/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 3 | 10 | 0.02 | 218 | 0.02 | `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | single | 4 | 60 | 1 | 6.96 | 1 | `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/param_matched_single_graph_5seed_update60_candidate_test50/param_matched_single/test_checkpoint_summary.csv`
- Episode rows: `results/param_matched_single_graph_5seed_update60_candidate_test50/param_matched_single/test_episode_metrics.csv`
- Selected checkpoints: `results/param_matched_single_graph_5seed_update60_candidate_test50/param_matched_single/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 5