# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T11:46:56

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0, 1, 2]
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['relay_failure']
episodes = 20
base_seed = 640000
strict_target_sensing = True
selection_csv = results/intercept_3d_strict_sensing_fair_30update_diag/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 0 | 30 | 0.15 | 89 | 0.15 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| relay_failure | multi_relation | 1 | 15 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0015.pt` |
| relay_failure | multi_relation | 2 | 15 | 0.05 | 155 | 0.05 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0015.pt` |
| relay_failure | no_graph | 0 | 20 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0020.pt` |
| relay_failure | no_graph | 1 | 30 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0030.pt` |
| relay_failure | no_graph | 2 | 30 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0030.pt` |
| relay_failure | single | 0 | 10 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed0/actor_critic_update_0010.pt` |
| relay_failure | single | 1 | 30 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt` |
| relay_failure | single | 2 | 5 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed2/actor_critic_update_0005.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_fair_30update_weaving_mild_probe/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_fair_30update_weaving_mild_probe/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_fair_30update_weaving_mild_probe/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9