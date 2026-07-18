# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T10:06:45

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
graph_encoders = ['single', 'multi_relation']
scenarios = ['relay_failure']
episodes = 5
base_seed = 320000
strict_target_sensing = True
selection_csv = none
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 0 | 3 | 0 | inf | 0 | `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0003.pt` |
| relay_failure | single | 0 | 3 | 0 | inf | 0 | `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke/runs/single/bc_ppo_seed0/actor_critic_update_0003.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_fair_staged_source_dev_seed0/stage4_strict_smoke/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6