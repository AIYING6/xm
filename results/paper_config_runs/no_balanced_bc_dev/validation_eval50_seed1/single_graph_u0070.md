# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:06:54

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed1/single_graph/actor_critic_update_0070.pt
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
| `success` | 0.34 |
| `chain_closed` | 0.34 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.0103091 |
| `tracking_rate` | 0.197187 |
| `comm_connectivity` | 0.44067 |
| `mean_message_age` | 56.5365 |
| `collision` | 0 |
| `timeout` | 0.66 |
| `constraint_violation` | 0 |
| `steps` | 186.86 |
| `first_attack_window_step` | 16.28 |
| `first_chain_close_step` | 14.6 |
| `post_failure_chain_recovered` | 0.34 |
| `post_failure_chain_recovery_steps` | 161.86 |
| `post_failure_chain_recovery_steps_censored` | 161.86 |
| `post_failure_chain_recovered_only_steps` | 6.1 |
| `chain_closed_during_failure_rate` | 0.0163074 |
| `tracking_during_failure_rate` | 0.425907 |
| `connectivity_during_failure` | 0.10025 |
| `avg_mean_range` | 30792.6 |
| `episode_min_blue_red_distance` | 2004.87 |
| `episode_min_blue_blue_distance` | 4550.67 |
| `final_min_blue_red_distance` | 53799.2 |
| `final_min_blue_blue_distance` | 4986.74 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
