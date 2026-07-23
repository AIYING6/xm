# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:28:57

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev60/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt
episodes = 50
target_policy = weaving_mild
communication_range_scale = 1.0
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
failed_blue_agent = -1
node_failure_start_step = 0
node_failure_duration_steps = 0
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.58 |
| `chain_closed` | 0.58 |
| `attack_window_formed` | 0.58 |
| `attack_window_rate` | 0.00624754 |
| `tracking_rate` | 0.311019 |
| `comm_connectivity` | 0.695453 |
| `mean_message_age` | 34.3004 |
| `collision` | 0 |
| `timeout` | 0.42 |
| `constraint_violation` | 0 |
| `steps` | 184.18 |
| `first_attack_window_step` | 72.8 |
| `first_chain_close_step` | 74.56 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 15029.1 |
| `episode_min_blue_red_distance` | 3552.53 |
| `episode_min_blue_blue_distance` | 1252.65 |
| `final_min_blue_red_distance` | 5383.65 |
| `final_min_blue_blue_distance` | 11445 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
