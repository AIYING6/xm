# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:43:12

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
| `success` | 0.333333 |
| `chain_closed` | 0.333333 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.00891262 |
| `tracking_rate` | 0.244151 |
| `comm_connectivity` | 0.424949 |
| `mean_message_age` | 80.8514 |
| `collision` | 0 |
| `timeout` | 0.666667 |
| `constraint_violation` | 0 |
| `steps` | 195.933 |
| `first_attack_window_step` | 21.2 |
| `first_chain_close_step` | 21.9333 |
| `post_failure_chain_recovered` | 0.333333 |
| `post_failure_chain_recovery_steps` | 155.933 |
| `post_failure_chain_recovery_steps_censored` | 155.933 |
| `post_failure_chain_recovered_only_steps` | 8.6 |
| `chain_closed_during_failure_rate` | 0.0308754 |
| `tracking_during_failure_rate` | 0.474268 |
| `connectivity_during_failure` | 0.170278 |
| `avg_mean_range` | 17274.1 |
| `episode_min_blue_red_distance` | 2104.78 |
| `episode_min_blue_blue_distance` | 2053.85 |
| `final_min_blue_red_distance` | 10226.8 |
| `final_min_blue_blue_distance` | 8397.26 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
