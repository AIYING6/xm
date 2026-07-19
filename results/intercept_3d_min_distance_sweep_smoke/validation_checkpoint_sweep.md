# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T03:12:19

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 1
base_seed = 291000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 60 | 1 | 4 | 1 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_min_distance_sweep_smoke/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_min_distance_sweep_smoke/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_min_distance_sweep_smoke/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6