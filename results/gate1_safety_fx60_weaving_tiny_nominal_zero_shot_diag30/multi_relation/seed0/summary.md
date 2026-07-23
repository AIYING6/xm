# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:39:12

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0060.pt
episodes = 30
target_policy = weaving_tiny
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
| `success` | 0.666667 |
| `chain_closed` | 0.666667 |
| `attack_window_formed` | 0.666667 |
| `attack_window_rate` | 0.00604592 |
| `tracking_rate` | 0.287928 |
| `comm_connectivity` | 0.582465 |
| `mean_message_age` | 39.0591 |
| `collision` | 0.0333333 |
| `timeout` | 0.3 |
| `constraint_violation` | 0 |
| `steps` | 203.6 |
| `first_attack_window_step` | 114.533 |
| `first_chain_close_step` | 117.8 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 16528.5 |
| `episode_min_blue_red_distance` | 3764.7 |
| `episode_min_blue_blue_distance` | 768.235 |
| `final_min_blue_red_distance` | 5415.48 |
| `final_min_blue_blue_distance` | 12308.1 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
