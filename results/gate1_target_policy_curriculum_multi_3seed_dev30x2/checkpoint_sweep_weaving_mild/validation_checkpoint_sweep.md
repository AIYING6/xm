# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T15:32:23

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2]
graph_encoders = ['multi_relation']
scenarios = ['nominal']
episodes = 30
base_seed = 406000
strict_target_sensing = False
agent_target_info_bottleneck = False
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| nominal | multi_relation | 0 | 30 | -1 | inf | 0.6 | `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/stage02_weaving_mild/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt` |
| nominal | multi_relation | 1 | 30 | -1 | inf | 0 | `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/stage02_weaving_mild/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0030.pt` |
| nominal | multi_relation | 2 | 20 | -1 | inf | 0.3 | `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/stage02_weaving_mild/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/checkpoint_sweep_weaving_mild/validation_checkpoint_summary.csv`
- Episode rows: `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/checkpoint_sweep_weaving_mild/validation_episode_metrics.csv`
- Selected checkpoints: `results/gate1_target_policy_curriculum_multi_3seed_dev30x2/checkpoint_sweep_weaving_mild/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 9