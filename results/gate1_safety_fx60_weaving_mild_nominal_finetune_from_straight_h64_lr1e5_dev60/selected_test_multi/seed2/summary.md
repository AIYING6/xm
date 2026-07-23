# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:30:37

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev60/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0030.pt
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
| `success` | 0.16 |
| `chain_closed` | 0.16 |
| `attack_window_formed` | 0.16 |
| `attack_window_rate` | 0.00146 |
| `tracking_rate` | 0.226382 |
| `comm_connectivity` | 0.36034 |
| `mean_message_age` | 61.8417 |
| `collision` | 0 |
| `timeout` | 0.84 |
| `constraint_violation` | 0 |
| `steps` | 247.1 |
| `first_attack_window_step` | 27.1 |
| `first_chain_close_step` | 27.86 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 23114.8 |
| `episode_min_blue_red_distance` | 6353.22 |
| `episode_min_blue_blue_distance` | 628.242 |
| `final_min_blue_red_distance` | 14310.7 |
| `final_min_blue_blue_distance` | 17979.7 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
