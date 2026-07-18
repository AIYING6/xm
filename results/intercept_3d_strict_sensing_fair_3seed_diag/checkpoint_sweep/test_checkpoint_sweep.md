# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T10:45:48

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
episodes = 10
base_seed = 530000
strict_target_sensing = True
selection_csv = results/intercept_3d_strict_sensing_fair_3seed_diag/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 0 | 10 | 1 | 5.6 | 1 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0010.pt` |
| relay_failure | multi_relation | 1 | 10 | 1 | 5.7 | 1 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| relay_failure | multi_relation | 2 | 10 | 1 | 5.5 | 1 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0010.pt` |
| relay_failure | no_graph | 0 | 10 | 0.3 | 5 | 0.3 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0010.pt` |
| relay_failure | no_graph | 1 | 10 | 0.9 | 5.33333 | 0.9 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0010.pt` |
| relay_failure | no_graph | 2 | 10 | 0 | inf | 0 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0010.pt` |
| relay_failure | single | 0 | 10 | 1 | 5.2 | 1 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/single/bc_ppo_seed0/actor_critic_update_0010.pt` |
| relay_failure | single | 1 | 2 | 0.8 | 4.75 | 0.8 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/single/bc_ppo_seed1/actor_critic_update_0002.pt` |
| relay_failure | single | 2 | 10 | 1 | 5.2 | 1 | `results/intercept_3d_strict_sensing_fair_3seed_diag/runs/single/bc_ppo_seed2/actor_critic_update_0010.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_strict_sensing_fair_3seed_diag/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_strict_sensing_fair_3seed_diag/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_strict_sensing_fair_3seed_diag/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9