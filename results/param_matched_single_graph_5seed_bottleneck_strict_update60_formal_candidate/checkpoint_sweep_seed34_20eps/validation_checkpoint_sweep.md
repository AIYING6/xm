# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T04:30:37

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [3, 4]
graph_encoders = ['single']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 368000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | single | 3 | 10 | 0.05 | 215 | 0.05 | `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0010.pt` |
| dropout030_relay_failure | single | 4 | 60 | 1 | 7 | 1 | `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/checkpoint_sweep_seed34_20eps/validation_checkpoint_summary.csv`
- Episode rows: `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/checkpoint_sweep_seed34_20eps/validation_episode_metrics.csv`
- Selected checkpoints: `results/param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate/checkpoint_sweep_seed34_20eps/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 12