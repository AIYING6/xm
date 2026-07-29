# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:55:24

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/mappo/actor_critic_update_0050.pt
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
| `success` | 0.28 |
| `chain_closed` | 0.28 |
| `attack_window_formed` | 0.36 |
| `attack_window_rate` | 0.00845178 |
| `tracking_rate` | 0.16765 |
| `comm_connectivity` | 0.459894 |
| `mean_message_age` | 52.2215 |
| `collision` | 0 |
| `timeout` | 0.72 |
| `constraint_violation` | 0 |
| `steps` | 199.84 |
| `first_attack_window_step` | 14.7 |
| `first_chain_close_step` | 11.92 |
| `post_failure_chain_recovered` | 0.28 |
| `post_failure_chain_recovery_steps` | 174.84 |
| `post_failure_chain_recovery_steps_censored` | 174.84 |
| `post_failure_chain_recovered_only_steps` | 4.92 |
| `chain_closed_during_failure_rate` | 0.0132597 |
| `tracking_during_failure_rate` | 0.370872 |
| `connectivity_during_failure` | 0.101958 |
| `avg_mean_range` | 32325.8 |
| `episode_min_blue_red_distance` | 1720.87 |
| `episode_min_blue_blue_distance` | 3908.31 |
| `final_min_blue_red_distance` | 58802.1 |
| `final_min_blue_blue_distance` | 4527.09 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
