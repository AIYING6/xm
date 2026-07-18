# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-16T23:31:16

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
episodes = 1
base_seed = 130000
strict_target_sensing = True
selection_csv = results/intercept_3d_strict_sensing_formal_smoke/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | single | 0 | 1 | 1 | 4 | 1 | `results/intercept_3d_strict_sensing_formal_smoke/runs/single/bc_ppo_seed0/actor_critic_update_0001.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_formal_smoke/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_formal_smoke/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_formal_smoke/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 1