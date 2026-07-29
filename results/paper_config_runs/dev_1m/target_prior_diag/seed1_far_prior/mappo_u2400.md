# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:39:43

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
| `success` | 0.933333 |
| `chain_closed` | 0.933333 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0210416 |
| `tracking_rate` | 0.276726 |
| `comm_connectivity` | 0.667329 |
| `mean_message_age` | 77.4212 |
| `collision` | 0 |
| `timeout` | 0.0666667 |
| `constraint_violation` | 0 |
| `steps` | 73.0333 |
| `first_attack_window_step` | 56.6333 |
| `first_chain_close_step` | 55.6333 |
| `post_failure_chain_recovered` | 0.933333 |
| `post_failure_chain_recovery_steps` | 33.0333 |
| `post_failure_chain_recovery_steps_censored` | 33.0333 |
| `post_failure_chain_recovered_only_steps` | 18.3 |
| `chain_closed_during_failure_rate` | 0.04617 |
| `tracking_during_failure_rate` | 0.552946 |
| `connectivity_during_failure` | 0.132672 |
| `avg_mean_range` | 14718.5 |
| `episode_min_blue_red_distance` | 3891.92 |
| `episode_min_blue_blue_distance` | 3703.49 |
| `final_min_blue_red_distance` | 5159.87 |
| `final_min_blue_blue_distance` | 5221.64 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
