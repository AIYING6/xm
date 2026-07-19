# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T17:33:39

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [4]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure_early', 'dropout030_relay_failure']
episodes = 100
base_seed = 260000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 60 | 0.57 | 5.52632 | 0.57 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 1 | 60 | 0.91 | 6.07692 | 0.91 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.37 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 60 | 0.92 | 38.1957 | 0.92 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 4 | 60 | 1 | 6.83 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 1 | 60 | 0.93 | 5.70968 | 0.93 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 4 | 60 | 0.16 | 4.3125 | 0.16 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.72 | 5.97222 | 0.72 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0.33 | 6.54545 | 0.33 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 3 | 60 | 0.7 | 5.55714 | 0.7 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 4 | 60 | 0.94 | 6 | 0.94 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 0 | 60 | 0.57 | 20.4912 | 0.57 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 1 | 60 | 0.91 | 21.0879 | 0.91 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 2 | 60 | 1 | 20.36 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 3 | 60 | 0.93 | 46.2366 | 0.93 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 4 | 60 | 1 | 20.61 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 0 | 60 | 0.01 | 220 | 0.01 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 1 | 60 | 0.97 | 20.6289 | 0.97 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 4 | 60 | 0.18 | 19.4444 | 0.18 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 0 | 60 | 0.74 | 20.9459 | 0.74 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 1 | 60 | 0.14 | 21.7143 | 0.14 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 3 | 60 | 0.54 | 20.6481 | 0.54 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 4 | 60 | 0.91 | 20.9341 | 0.91 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_safety_fx60_failure_timing_generalization_formal/test_checkpoint_summary.csv`
- Episode rows: `results/gate1_safety_fx60_failure_timing_generalization_formal/test_episode_metrics.csv`
- Selected checkpoints: `results/gate1_safety_fx60_failure_timing_generalization_formal/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 35