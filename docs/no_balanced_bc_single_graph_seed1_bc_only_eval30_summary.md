# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T02:06:37

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_seed1/single_graph/actor_critic_latest.pt
episodes = 30
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.3
message_delay_steps = 2
radar_dropout_prob = 0.0
failed_blue_agent = 1
node_failure_start_step = 25
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
| `success` | 0.333333 |
| `chain_closed` | 0.333333 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.0103316 |
| `tracking_rate` | 0.200167 |
| `comm_connectivity` | 0.449806 |
| `mean_message_age` | 55.0129 |
| `collision` | 0 |
| `timeout` | 0.666667 |
| `constraint_violation` | 0 |
| `steps` | 188.167 |
| `first_attack_window_step` | 19.1 |
| `first_chain_close_step` | 14.1667 |
| `post_failure_chain_recovered` | 0.333333 |
| `post_failure_chain_recovery_steps` | 163.167 |
| `post_failure_chain_recovery_steps_censored` | 163.167 |
| `post_failure_chain_recovered_only_steps` | 5.83333 |
| `chain_closed_during_failure_rate` | 0.0162771 |
| `tracking_during_failure_rate` | 0.437658 |
| `connectivity_during_failure` | 0.102569 |
| `avg_mean_range` | 31029.8 |
| `episode_min_blue_red_distance` | 1928.71 |
| `episode_min_blue_blue_distance` | 4393.25 |
| `final_min_blue_red_distance` | 54118.9 |
| `final_min_blue_blue_distance` | 4789.53 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
