# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T21:51:25

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2, 3, 4]
graph_encoders = ['no_graph', 'single', 'multi_relation']
scenarios = ['dropout030_scout_failure']
episodes = 20
base_seed = 351000
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
| dropout030_scout_failure | multi_relation | 0 | 60 | 0.6 | 5.16667 | 0.6 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_scout_failure | multi_relation | 1 | 60 | 0.8 | 6 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_scout_failure | multi_relation | 2 | 60 | 1 | 5.35 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_scout_failure | multi_relation | 3 | 60 | 0.4 | 5.625 | 0.4 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_scout_failure | multi_relation | 4 | 60 | 1 | 5.65 | 1 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_scout_failure | no_graph | 0 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_scout_failure | no_graph | 1 | 60 | 0.95 | 5.47368 | 0.95 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_scout_failure | no_graph | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_scout_failure | no_graph | 3 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_scout_failure | no_graph | 4 | 60 | 0.25 | 4.4 | 0.25 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/no_graph/bc_ppo_seed4/actor_critic_update_0060.pt` |
| dropout030_scout_failure | single | 0 | 60 | 0.8 | 6.625 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_scout_failure | single | 1 | 60 | 0.3 | 7 | 0.3 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed1/actor_critic_update_0060.pt` |
| dropout030_scout_failure | single | 2 | 60 | 0 | inf | 0 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed2/actor_critic_update_0060.pt` |
| dropout030_scout_failure | single | 3 | 60 | 0.65 | 5.76923 | 0.65 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed3/actor_critic_update_0060.pt` |
| dropout030_scout_failure | single | 4 | 60 | 0.8 | 6.0625 | 0.8 | `results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/single/bc_ppo_seed4/actor_critic_update_0060.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_safety_fx60_dropout030_scout_failure_diag20/validation_checkpoint_summary.csv`
- Episode rows: `results/gate1_safety_fx60_dropout030_scout_failure_diag20/validation_episode_metrics.csv`
- Selected checkpoints: `results/gate1_safety_fx60_dropout030_scout_failure_diag20/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 15