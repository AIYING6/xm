# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T00:55:09

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/relation_bottleneck_dev/bc_seed0_dev200e12/actor_critic_latest.pt
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
| `success` | 0 |
| `chain_closed` | 0 |
| `attack_window_formed` | 0 |
| `attack_window_rate` | 0 |
| `tracking_rate` | 0.0278205 |
| `comm_connectivity` | 0.129274 |
| `mean_message_age` | 87.0685 |
| `collision` | 0 |
| `timeout` | 1 |
| `constraint_violation` | 0 |
| `steps` | 260 |
| `first_attack_window_step` | -1 |
| `first_chain_close_step` | -1 |
| `post_failure_chain_recovered` | 0 |
| `post_failure_chain_recovery_steps` | 235 |
| `post_failure_chain_recovery_steps_censored` | 235 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | 0 |
| `tracking_during_failure_rate` | 0.0568056 |
| `connectivity_during_failure` | 0.0763889 |
| `avg_mean_range` | 19068.1 |
| `episode_min_blue_red_distance` | 5258.21 |
| `episode_min_blue_blue_distance` | 870.135 |
| `final_min_blue_red_distance` | 10845.3 |
| `final_min_blue_blue_distance` | 28824.4 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
