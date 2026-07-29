# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T04:09:38

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1/actor_critic_update_2400.pt
episodes = 30
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.3
message_delay_steps = 2
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
| `success` | 0.966667 |
| `chain_closed` | 0.966667 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0216198 |
| `tracking_rate` | 0.251136 |
| `comm_connectivity` | 0.447937 |
| `mean_message_age` | 75.4806 |
| `collision` | 0 |
| `timeout` | 0.0333333 |
| `constraint_violation` | 0 |
| `steps` | 66.6333 |
| `first_attack_window_step` | 57 |
| `first_chain_close_step` | 57.9333 |
| `post_failure_chain_recovered` | 0.966667 |
| `post_failure_chain_recovery_steps` | 26.6333 |
| `post_failure_chain_recovery_steps_censored` | 26.6333 |
| `post_failure_chain_recovered_only_steps` | 19.2667 |
| `chain_closed_during_failure_rate` | 0.0475001 |
| `tracking_during_failure_rate` | 0.454392 |
| `connectivity_during_failure` | 0.148542 |
| `avg_mean_range` | 14634.9 |
| `episode_min_blue_red_distance` | 3720.41 |
| `episode_min_blue_blue_distance` | 3674.52 |
| `final_min_blue_red_distance` | 4535.83 |
| `final_min_blue_blue_distance` | 4091.9 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
