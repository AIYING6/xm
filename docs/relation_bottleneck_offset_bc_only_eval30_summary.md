# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T00:56:06

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/relation_bottleneck_dev/bc_seed0_offset_dev200e12/actor_critic_latest.pt
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
multi_relation_global_residual_weight = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.0333333 |
| `chain_closed` | 0.0333333 |
| `attack_window_formed` | 0.0333333 |
| `attack_window_rate` | 0.000838574 |
| `tracking_rate` | 0.0610152 |
| `comm_connectivity` | 0.124782 |
| `mean_message_age` | 82.9675 |
| `collision` | 0 |
| `timeout` | 0.966667 |
| `constraint_violation` | 0 |
| `steps` | 253.1 |
| `first_attack_window_step` | 0.7 |
| `first_chain_close_step` | 0.8 |
| `post_failure_chain_recovered` | 0.0333333 |
| `post_failure_chain_recovery_steps` | 228.1 |
| `post_failure_chain_recovery_steps_censored` | 228.1 |
| `post_failure_chain_recovered_only_steps` | -0.0333333 |
| `chain_closed_during_failure_rate` | 0.00114943 |
| `tracking_during_failure_rate` | 0.149071 |
| `connectivity_during_failure` | 0.117888 |
| `avg_mean_range` | 31776.4 |
| `episode_min_blue_red_distance` | 2778.32 |
| `episode_min_blue_blue_distance` | 1100.73 |
| `final_min_blue_red_distance` | 55572.5 |
| `final_min_blue_blue_distance` | 36385.8 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
