# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T12:08:57

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [4]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 20
base_seed = 390000
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
| dropout030_relay_failure | multi_relation | 4 | 40 | 0.8 | 5.1875 | 0.8 | `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0040.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/checkpoint_sweep_seed4_formal/validation_checkpoint_summary.csv`
- Episode rows: `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/checkpoint_sweep_seed4_formal/validation_episode_metrics.csv`
- Selected checkpoints: `results/true_no_role_identity_hardened_5seed_strict_update60_formal_candidate/checkpoint_sweep_seed4_formal/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6