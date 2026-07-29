# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:42:01

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed2/actor_critic_update_0040.pt
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
| `attack_window_formed` | 0.866667 |
| `attack_window_rate` | 0.0148619 |
| `tracking_rate` | 0.133979 |
| `comm_connectivity` | 0.538484 |
| `mean_message_age` | 69.4436 |
| `collision` | 0 |
| `timeout` | 0.466667 |
| `constraint_violation` | 0 |
| `steps` | 155.533 |
| `first_attack_window_step` | 45.8667 |
| `first_chain_close_step` | 33.7333 |
| `post_failure_chain_recovered` | 0.533333 |
| `post_failure_chain_recovery_steps` | 115.533 |
| `post_failure_chain_recovery_steps_censored` | 115.533 |
| `post_failure_chain_recovered_only_steps` | 12.4 |
| `chain_closed_during_failure_rate` | 0.0512083 |
| `tracking_during_failure_rate` | 0.244389 |
| `connectivity_during_failure` | 0.276389 |
| `avg_mean_range` | 18400.1 |
| `episode_min_blue_red_distance` | 2800.13 |
| `episode_min_blue_blue_distance` | 2469.18 |
| `final_min_blue_red_distance` | 13051.2 |
| `final_min_blue_blue_distance` | 10417.8 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
