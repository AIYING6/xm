# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T03:06:33

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
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 280000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/intercept_3d_gate1_hardened_60update_safety_diag/checkpoint_sweep/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 30 | 0.8 | 5.8 | 0.8 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| dropout030_relay_failure | multi_relation | 1 | 10 | 0.82 | 6 | 0.82 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 2 | 10 | 0.98 | 5.55102 | 0.98 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 0 | 10 | 0.04 | 5 | 0.04 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0010.pt` |
| dropout030_relay_failure | no_graph | 1 | 30 | 0.8 | 5.2 | 0.8 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/no_graph/bc_ppo_seed1/actor_critic_update_0030.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 50 | 0.82 | 5.78049 | 0.82 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/single/bc_ppo_seed0/actor_critic_update_0050.pt` |
| dropout030_relay_failure | single | 1 | 30 | 0.1 | 7.6 | 0.1 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt` |
| dropout030_relay_failure | single | 2 | 20 | 0.68 | 5.85294 | 0.68 | `results/intercept_3d_gate1_hardened_60update_safety_diag/runs/single/bc_ppo_seed2/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/intercept_3d_gate1_hardened_60update_safety_diag/checkpoint_sweep/test_checkpoint_summary.csv`
- Episode rows: `results/intercept_3d_gate1_hardened_60update_safety_diag/checkpoint_sweep/test_episode_metrics.csv`
- Selected checkpoints: `results/intercept_3d_gate1_hardened_60update_safety_diag/checkpoint_sweep/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9