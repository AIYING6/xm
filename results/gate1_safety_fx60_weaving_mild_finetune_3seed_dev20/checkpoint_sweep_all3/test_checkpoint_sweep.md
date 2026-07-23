# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T12:54:52

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
graph_encoders = ['single', 'multi_relation']
scenarios = ['dropout030_relay_failure']
episodes = 10
base_seed = 394000
strict_target_sensing = True
agent_target_info_bottleneck = True
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/checkpoint_sweep_all3/validation_selected_checkpoints.csv
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_relay_failure | multi_relation | 0 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 1 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | multi_relation | 2 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 0 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/single/bc_ppo_seed0/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 1 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/single/bc_ppo_seed1/actor_critic_update_0020.pt` |
| dropout030_relay_failure | single | 2 | 20 | 0 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/runs/single/bc_ppo_seed2/actor_critic_update_0020.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/checkpoint_sweep_all3/test_checkpoint_summary.csv`
- Episode rows: `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/checkpoint_sweep_all3/test_episode_metrics.csv`
- Selected checkpoints: `results/gate1_safety_fx60_weaving_mild_finetune_3seed_dev20/checkpoint_sweep_all3/test_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6