# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:40:47

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed1/actor_critic_update_2200.pt
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
| `success` | 0.3 |
| `chain_closed` | 0.3 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.00922821 |
| `tracking_rate` | 0.237534 |
| `comm_connectivity` | 0.416558 |
| `mean_message_age` | 83.027 |
| `collision` | 0 |
| `timeout` | 0.7 |
| `constraint_violation` | 0 |
| `steps` | 196.633 |
| `first_attack_window_step` | 21.2 |
| `first_chain_close_step` | 13.9333 |
| `post_failure_chain_recovered` | 0.3 |
| `post_failure_chain_recovery_steps` | 156.633 |
| `post_failure_chain_recovery_steps_censored` | 156.633 |
| `post_failure_chain_recovered_only_steps` | 1.93333 |
| `chain_closed_during_failure_rate` | 0.0308754 |
| `tracking_during_failure_rate` | 0.472601 |
| `connectivity_during_failure` | 0.150417 |
| `avg_mean_range` | 17611.9 |
| `episode_min_blue_red_distance` | 2073.96 |
| `episode_min_blue_blue_distance` | 2193.44 |
| `final_min_blue_red_distance` | 10899.1 |
| `final_min_blue_blue_distance` | 8692.75 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
