# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:05:40

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed1/single_graph/actor_critic_update_0030.pt
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
| `success` | 0.32 |
| `chain_closed` | 0.32 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.00971647 |
| `tracking_rate` | 0.189156 |
| `comm_connectivity` | 0.448592 |
| `mean_message_age` | 54.5613 |
| `collision` | 0 |
| `timeout` | 0.68 |
| `constraint_violation` | 0 |
| `steps` | 191.16 |
| `first_attack_window_step` | 16.3 |
| `first_chain_close_step` | 13.68 |
| `post_failure_chain_recovered` | 0.32 |
| `post_failure_chain_recovery_steps` | 166.16 |
| `post_failure_chain_recovery_steps_censored` | 166.16 |
| `post_failure_chain_recovered_only_steps` | 5.68 |
| `chain_closed_during_failure_rate` | 0.015355 |
| `tracking_during_failure_rate` | 0.411881 |
| `connectivity_during_failure` | 0.102708 |
| `avg_mean_range` | 31276.4 |
| `episode_min_blue_red_distance` | 1964.75 |
| `episode_min_blue_blue_distance` | 4582.23 |
| `final_min_blue_red_distance` | 55527.1 |
| `final_min_blue_blue_distance` | 5071.3 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
