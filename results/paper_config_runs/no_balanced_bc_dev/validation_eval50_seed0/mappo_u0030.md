# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:20:10

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/mappo/actor_critic_update_0030.pt
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
| `success` | 0.2 |
| `chain_closed` | 0.2 |
| `attack_window_formed` | 0.36 |
| `attack_window_rate` | 0.00632506 |
| `tracking_rate` | 0.141885 |
| `comm_connectivity` | 0.47656 |
| `mean_message_age` | 47.6798 |
| `collision` | 0 |
| `timeout` | 0.8 |
| `constraint_violation` | 0 |
| `steps` | 217.02 |
| `first_attack_window_step` | 14.7 |
| `first_chain_close_step` | 8.22 |
| `post_failure_chain_recovered` | 0.2 |
| `post_failure_chain_recovery_steps` | 192.02 |
| `post_failure_chain_recovery_steps_censored` | 192.02 |
| `post_failure_chain_recovered_only_steps` | 3.22 |
| `chain_closed_during_failure_rate` | 0.00949351 |
| `tracking_during_failure_rate` | 0.328895 |
| `connectivity_during_failure` | 0.11125 |
| `avg_mean_range` | 34254.1 |
| `episode_min_blue_red_distance` | 1577.25 |
| `episode_min_blue_blue_distance` | 3738.27 |
| `final_min_blue_red_distance` | 64889.2 |
| `final_min_blue_blue_distance` | 4393.92 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
