# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-19T16:42:49

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = test
seeds = [0, 1, 2, 3, 4]
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_relay_failure_early', 'dropout030_relay_failure', 'dropout030_relay_failure_late']
episodes = 5
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
| dropout030_relay_failure | multi_relation | 0 | 60 | 0.4 | 5.5 | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 1 | 60 | 0.8 | 6.25 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.4 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 60 | 1 | 47.8 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 4 | 60 | 1 | 5.6 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 1 | 60 | 1 | 5.6 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | no_graph | 4 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 0 | 60 | 0.8 | 6.25 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 1 | 60 | 0.4 | 7 | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 3 | 60 | 0.8 | 5 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure | single | 4 | 60 | 0.8 | 6 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 0 | 60 | 0.2 | 19 | 0.2 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 1 | 60 | 0.8 | 21.25 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 2 | 60 | 1 | 20.4 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 3 | 60 | 0.8 | 46.5 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | multi_relation | 4 | 60 | 1 | 20.4 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 1 | 60 | 1 | 20.6 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | no_graph | 4 | 60 | 0.4 | 21 | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 0 | 60 | 0.6 | 20.6667 | 0.6 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 1 | 60 | 0.2 | 22 | 0.2 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 3 | 60 | 0.8 | 20 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_early | single | 4 | 60 | 0.8 | 20.5 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | multi_relation | 0 | 60 | 0 | inf | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | multi_relation | 1 | 60 | 0 | inf | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | multi_relation | 2 | 60 | 0 | inf | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | multi_relation | 3 | 60 | 0.2 | 88 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | multi_relation | 4 | 60 | 0 | inf | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | no_graph | 1 | 60 | 0 | inf | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | no_graph | 4 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | single | 0 | 60 | 0 | inf | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | single | 1 | 60 | 0 | inf | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | single | 3 | 60 | 0 | inf | 0.6 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_relay_failure_late | single | 4 | 60 | 0 | inf | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_safety_fx60_failure_timing_generalization_diag5/test_checkpoint_summary.csv`
- Episode rows: `results/gate1_safety_fx60_failure_timing_generalization_diag5/test_episode_metrics.csv`
- Selected checkpoints: `results/gate1_safety_fx60_failure_timing_generalization_diag5/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 45