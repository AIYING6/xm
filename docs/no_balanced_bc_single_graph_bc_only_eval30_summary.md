# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:22:11

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_seed0/single_graph/actor_critic_latest.pt
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
| `success` | 0.3 |
| `chain_closed` | 0.3 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.00949365 |
| `tracking_rate` | 0.18982 |
| `comm_connectivity` | 0.452255 |
| `mean_message_age` | 52.9247 |
| `collision` | 0 |
| `timeout` | 0.7 |
| `constraint_violation` | 0 |
| `steps` | 195.3 |
| `first_attack_window_step` | 19.1 |
| `first_chain_close_step` | 12.6 |
| `post_failure_chain_recovered` | 0.3 |
| `post_failure_chain_recovery_steps` | 170.3 |
| `post_failure_chain_recovery_steps_censored` | 170.3 |
| `post_failure_chain_recovered_only_steps` | 5.1 |
| `chain_closed_during_failure_rate` | 0.0147619 |
| `tracking_during_failure_rate` | 0.423757 |
| `connectivity_during_failure` | 0.107639 |
| `avg_mean_range` | 31899.3 |
| `episode_min_blue_red_distance` | 1771.75 |
| `episode_min_blue_blue_distance` | 4724.73 |
| `final_min_blue_red_distance` | 57015.4 |
| `final_min_blue_blue_distance` | 5090.48 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
