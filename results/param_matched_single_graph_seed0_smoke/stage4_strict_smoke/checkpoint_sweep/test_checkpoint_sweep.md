# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T03:14:27

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0]
graph_encoders = ['single']
scenarios = ['relay_failure']
episodes = 5
base_seed = 361000
strict_target_sensing = True
agent_target_info_bottleneck = False
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/param_matched_single_graph_seed0_smoke/stage4_strict_smoke/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | single | 0 | 2 | 0 | inf | 0 | `results/param_matched_single_graph_seed0_smoke/stage4_strict_smoke/runs/single/bc_ppo_seed0/actor_critic_update_0002.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/param_matched_single_graph_seed0_smoke/stage4_strict_smoke/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/param_matched_single_graph_seed0_smoke/stage4_strict_smoke/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/param_matched_single_graph_seed0_smoke/stage4_strict_smoke/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 1