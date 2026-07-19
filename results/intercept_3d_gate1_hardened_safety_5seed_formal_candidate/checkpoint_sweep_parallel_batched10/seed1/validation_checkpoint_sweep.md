# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T05:28:12

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
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 300000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = 0.0
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 1 | 50 | 0.98 | 6.40816 | 0.98 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0050.pt` |
| dropout030_relay_failure | no_graph | 1 | 50 | 0.98 | 5.95918 | 0.98 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 1 | 50 | 0.38 | 6.68421 | 0.38 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0050.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_parallel_batched10/seed1/validation_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_parallel_batched10/seed1/validation_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_parallel_batched10/seed1/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 18