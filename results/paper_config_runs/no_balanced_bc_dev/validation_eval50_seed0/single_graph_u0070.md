# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:19:25

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/single_graph/actor_critic_update_0070.pt
episodes = 50
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
| `success` | 0.38 |
| `chain_closed` | 0.38 |
| `attack_window_formed` | 0.7 |
| `attack_window_rate` | 0.0120334 |
| `tracking_rate` | 0.209324 |
| `comm_connectivity` | 0.263011 |
| `mean_message_age` | 69.3633 |
| `collision` | 0 |
| `timeout` | 0.62 |
| `constraint_violation` | 0 |
| `steps` | 178.22 |
| `first_attack_window_step` | 29.82 |
| `first_chain_close_step` | 16.4 |
| `post_failure_chain_recovered` | 0.38 |
| `post_failure_chain_recovery_steps` | 153.22 |
| `post_failure_chain_recovery_steps_censored` | 153.22 |
| `post_failure_chain_recovered_only_steps` | 6.9 |
| `chain_closed_during_failure_rate` | 0.018303 |
| `tracking_during_failure_rate` | 0.442274 |
| `connectivity_during_failure` | 0.180917 |
| `avg_mean_range` | 28602.3 |
| `episode_min_blue_red_distance` | 2156.13 |
| `episode_min_blue_blue_distance` | 1292.57 |
| `final_min_blue_red_distance` | 45951.9 |
| `final_min_blue_blue_distance` | 5637.91 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
