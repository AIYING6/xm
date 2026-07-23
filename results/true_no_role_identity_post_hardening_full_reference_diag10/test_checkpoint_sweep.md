# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T02:51:24

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
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure', 'scout_failure']
episodes = 10
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
| dropout030_relay_failure | multi_relation | 1 | 60 | 0.9 | 6.11111 | 0.9 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 1 | 5.5 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| scout_failure | multi_relation | 0 | 60 | 0.6 | 6.16667 | 0.6 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| scout_failure | multi_relation | 1 | 60 | 1 | 6.1 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| scout_failure | multi_relation | 2 | 60 | 1 | 5.4 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/true_no_role_identity_post_hardening_full_reference_diag10/test_checkpoint_summary.csv`
- Episode rows: `results/true_no_role_identity_post_hardening_full_reference_diag10/test_episode_metrics.csv`
- Selected checkpoints: `results/true_no_role_identity_post_hardening_full_reference_diag10/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6