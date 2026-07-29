# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:06:19

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed1/single_graph/actor_critic_update_0040.pt
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
| `success` | 0.24 |
| `chain_closed` | 0.24 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.00766693 |
| `tracking_rate` | 0.167433 |
| `comm_connectivity` | 0.468155 |
| `mean_message_age` | 49.6082 |
| `collision` | 0 |
| `timeout` | 0.76 |
| `constraint_violation` | 0 |
| `steps` | 208.26 |
| `first_attack_window_step` | 16.28 |
| `first_chain_close_step` | 9.9 |
| `post_failure_chain_recovered` | 0.24 |
| `post_failure_chain_recovery_steps` | 183.26 |
| `post_failure_chain_recovery_steps_censored` | 183.26 |
| `post_failure_chain_recovered_only_steps` | 3.9 |
| `chain_closed_during_failure_rate` | 0.0117619 |
| `tracking_during_failure_rate` | 0.382944 |
| `connectivity_during_failure` | 0.114625 |
| `avg_mean_range` | 33231.4 |
| `episode_min_blue_red_distance` | 1719.03 |
| `episode_min_blue_blue_distance` | 4683.3 |
| `final_min_blue_red_distance` | 61599.8 |
| `final_min_blue_blue_distance` | 5148.45 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
