# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-22T13:18:19

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
graph_encoders = ['single', 'multi_relation']
scenarios = ['nominal']
episodes = 20
base_seed = 396000
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
| nominal | multi_relation | 0 | -2 | -1 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/multi_relation/bc_ppo_seed0/actor_critic_best.pt` |
| nominal | multi_relation | 1 | -2 | -1 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/multi_relation/bc_ppo_seed1/actor_critic_best.pt` |
| nominal | multi_relation | 2 | -2 | -1 | inf | 0.05 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/multi_relation/bc_ppo_seed2/actor_critic_best.pt` |
| nominal | single | 0 | -2 | -1 | inf | 0 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/single/bc_ppo_seed0/actor_critic_best.pt` |
| nominal | single | 1 | -2 | -1 | inf | 0.2 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/single/bc_ppo_seed1/actor_critic_best.pt` |
| nominal | single | 2 | -2 | -1 | inf | 0.2 | `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage2_nominal/runs/single/bc_ppo_seed2/actor_critic_best.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/checkpoint_sweep_nominal_best/validation_checkpoint_summary.csv`
- Episode rows: `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/checkpoint_sweep_nominal_best/validation_episode_metrics.csv`
- Selected checkpoints: `results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/checkpoint_sweep_nominal_best/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 6