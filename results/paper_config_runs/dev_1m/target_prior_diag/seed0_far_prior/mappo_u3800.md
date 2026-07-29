# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:28:11

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed0/actor_critic_update_3800.pt
episodes = 30
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
multi_relation_global_residual_weight = 1.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.533333 |
| `chain_closed` | 0.533333 |
| `attack_window_formed` | 0.566667 |
| `attack_window_rate` | 0.0135439 |
| `tracking_rate` | 0.178583 |
| `comm_connectivity` | 0.559265 |
| `mean_message_age` | 43.0759 |
| `collision` | 0 |
| `timeout` | 0.466667 |
| `constraint_violation` | 0 |
| `steps` | 152.1 |
| `first_attack_window_step` | 30.6333 |
| `first_chain_close_step` | 30.3 |
| `post_failure_chain_recovered` | 0.533333 |
| `post_failure_chain_recovery_steps` | 112.1 |
| `post_failure_chain_recovery_steps_censored` | 112.1 |
| `post_failure_chain_recovered_only_steps` | 8.96667 |
| `chain_closed_during_failure_rate` | 0.0286344 |
| `tracking_during_failure_rate` | 0.288138 |
| `connectivity_during_failure` | 0.26875 |
| `avg_mean_range` | 15482.9 |
| `episode_min_blue_red_distance` | 3138.31 |
| `episode_min_blue_blue_distance` | 1951.82 |
| `final_min_blue_red_distance` | 11468.1 |
| `final_min_blue_blue_distance` | 5040.64 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
