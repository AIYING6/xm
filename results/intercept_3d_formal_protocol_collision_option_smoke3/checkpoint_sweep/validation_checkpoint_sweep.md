# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T15:39:38

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
graph_encoders = ['single']
scenarios = ['dropout030_relay_failure']
episodes = 1
base_seed = 889401
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = none
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | single | 0 | 1 | 1 | 9 | 1 | `results/intercept_3d_formal_protocol_collision_option_smoke3/runs/single/bc_ppo_seed0/actor_critic_update_0001.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_formal_protocol_collision_option_smoke3/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_formal_protocol_collision_option_smoke3/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_formal_protocol_collision_option_smoke3/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 1