# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T00:33:08

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [1]
graph_encoders = ['single', 'multi_relation']
scenarios = ['relay_failure']
episodes = 50
base_seed = 120000
strict_target_sensing = True
selection_csv = none
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 1 | 110 | 1 | 5.14 | 1 | `results/intercept_3d_strict_sensing_formal_seed1_dev/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0110.pt` |
| relay_failure | single | 1 | 10 | 0.92 | 5.52174 | 0.92 | `results/intercept_3d_strict_sensing_formal_seed1_dev/runs/single/bc_ppo_seed1/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_formal_seed1_dev/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_formal_seed1_dev/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_formal_seed1_dev/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 24