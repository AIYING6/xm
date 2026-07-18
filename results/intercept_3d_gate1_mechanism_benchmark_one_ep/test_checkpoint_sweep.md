# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-18T21:18:32

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
graph_encoders = ['no_graph']
scenarios = ['dropout030_relay_failure']
episodes = 1
base_seed = 760000
strict_target_sensing = True
agent_target_info_bottleneck = True
selection_csv = results/intercept_3d_gate1_dropout030_bottleneck_5seed_formal/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_post_change_retrain_60update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_mechanism_benchmark_one_ep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 1