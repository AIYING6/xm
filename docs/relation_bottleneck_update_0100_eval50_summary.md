# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:13:48

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/relation_bottleneck_dev/bc_unbalanced_ppo_seed0_dev100/actor_critic_update_0100.pt
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
multi_relation_global_residual_weight = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.26 |
| `chain_closed` | 0.26 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.0081826 |
| `tracking_rate` | 0.178276 |
| `comm_connectivity` | 0.470032 |
| `mean_message_age` | 49.7054 |
| `collision` | 0 |
| `timeout` | 0.74 |
| `constraint_violation` | 0 |
| `steps` | 203.96 |
| `first_attack_window_step` | 16.26 |
| `first_chain_close_step` | 10.82 |
| `post_failure_chain_recovered` | 0.26 |
| `post_failure_chain_recovery_steps` | 178.96 |
| `post_failure_chain_recovery_steps_censored` | 178.96 |
| `post_failure_chain_recovered_only_steps` | 4.32 |
| `chain_closed_during_failure_rate` | 0.0127143 |
| `tracking_during_failure_rate` | 0.405393 |
| `connectivity_during_failure` | 0.112083 |
| `avg_mean_range` | 32843.5 |
| `episode_min_blue_red_distance` | 1641.35 |
| `episode_min_blue_blue_distance` | 3381.53 |
| `final_min_blue_red_distance` | 60198.9 |
| `final_min_blue_blue_distance` | 4848.21 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
