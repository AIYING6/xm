# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T12:17:22

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
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 690000
strict_target_sensing = True
selection_csv = none
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 30 | 1 | 6.1 | 1 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | multi_relation | 1 | 15 | 0.9 | 5.38889 | 0.9 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0015.pt` |
| dropout030_relay_failure | multi_relation | 2 | 15 | 1 | 5.75 | 1 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0015.pt` |
| dropout030_relay_failure | no_graph | 0 | 5 | 0.25 | 4.4 | 0.25 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0005.pt` |
| dropout030_relay_failure | no_graph | 1 | 5 | 0.9 | 5.27778 | 0.9 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0005.pt` |
| dropout030_relay_failure | no_graph | 2 | 30 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 0 | 5 | 0.75 | 5 | 0.75 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0005.pt` |
| dropout030_relay_failure | single | 1 | 30 | 0.85 | 5.11765 | 0.85 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 2 | 5 | 1 | 5.3 | 1 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0005.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag/checkpoint_sweep/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag/checkpoint_sweep/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_fair_30update_dropout030_formal_diag/checkpoint_sweep/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 54