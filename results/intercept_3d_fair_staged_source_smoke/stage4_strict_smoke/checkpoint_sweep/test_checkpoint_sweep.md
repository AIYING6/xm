# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-17T02:11:47

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
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['relay_failure']
episodes = 1
base_seed = 330000
strict_target_sensing = True
selection_csv = results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/checkpoint_sweep/validation_selected_checkpoints.csv
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| relay_failure | multi_relation | 0 | 1 | 0 | inf | 0 | `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0001.pt` |
| relay_failure | no_graph | 0 | 1 | 0 | inf | 0 | `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/runs/no_graph/bc_ppo_seed0/actor_critic_update_0001.pt` |
| relay_failure | single | 0 | 1 | 0 | inf | 0 | `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/runs/single/bc_ppo_seed0/actor_critic_update_0001.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_fair_staged_source_smoke/stage4_strict_smoke/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 3