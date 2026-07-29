# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:27:53

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_3907.pt
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
| `success` | 0.866667 |
| `chain_closed` | 0.866667 |
| `attack_window_formed` | 0.933333 |
| `attack_window_rate` | 0.0196648 |
| `tracking_rate` | 0.426175 |
| `comm_connectivity` | 0.728292 |
| `mean_message_age` | 42.5529 |
| `collision` | 0 |
| `timeout` | 0.133333 |
| `constraint_violation` | 0 |
| `steps` | 86.3 |
| `first_attack_window_step` | 52.7 |
| `first_chain_close_step` | 51.5 |
| `post_failure_chain_recovered` | 0.866667 |
| `post_failure_chain_recovery_steps` | 46.3 |
| `post_failure_chain_recovery_steps_censored` | 46.3 |
| `post_failure_chain_recovered_only_steps` | 16.8333 |
| `chain_closed_during_failure_rate` | 0.042333 |
| `tracking_during_failure_rate` | 0.874375 |
| `connectivity_during_failure` | 0.311111 |
| `avg_mean_range` | 14834.5 |
| `episode_min_blue_red_distance` | 3973.53 |
| `episode_min_blue_blue_distance` | 1304.76 |
| `final_min_blue_red_distance` | 6643.77 |
| `final_min_blue_blue_distance` | 1972.89 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
