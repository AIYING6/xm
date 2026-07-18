# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T12:48:08

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2]
graph_encoders = ['single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 710000
strict_target_sensing = True
selection_csv = none
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 30 | 1 | 6.4 | 1 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.95 | 5.68421 | 0.95 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 30 | 1 | 5.3 | 1 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.85 | 5.35294 | 0.85 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 30 | 0.75 | 4.8 | 0.75 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 2 | 50 | 1 | 5.1 | 1 | `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/single/bc_ppo_seed2/actor_critic_update_0050.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 36