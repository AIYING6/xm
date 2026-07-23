# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T12:15:18

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
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 391000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/checkpoint_selection_all5_formal/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 10 | 0.4 | 6.05 | 0.4 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0010.pt` |
| dropout030_relay_failure | multi_relation | 1 | 60 | 0.66 | 5.75758 | 0.66 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 2 | 60 | 0.02 | 7 | 0.02 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_relay_failure | multi_relation | 3 | 20 | 0.88 | 5.54545 | 0.88 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 4 | 40 | 0.88 | 5.75 | 0.88 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0040.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/no_role_identity/test_checkpoint_summary.csv`
- Episode rows: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/no_role_identity/test_episode_metrics.csv`
- Selected checkpoints: `results/true_no_role_identity_hardened_5seed_update60_formal_test50/no_role_identity/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 5