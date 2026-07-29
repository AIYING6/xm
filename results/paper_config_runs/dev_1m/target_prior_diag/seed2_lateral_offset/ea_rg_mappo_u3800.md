# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:43:44

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed2/actor_critic_update_3800.pt
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
| `success` | 0.0333333 |
| `chain_closed` | 0.0333333 |
| `attack_window_formed` | 0.0666667 |
| `attack_window_rate` | 0.00128515 |
| `tracking_rate` | 0.187117 |
| `comm_connectivity` | 0.243714 |
| `mean_message_age` | 84.6365 |
| `collision` | 0 |
| `timeout` | 0.966667 |
| `constraint_violation` | 0 |
| `steps` | 253.633 |
| `first_attack_window_step` | 3.46667 |
| `first_chain_close_step` | 1.33333 |
| `post_failure_chain_recovered` | 0.0333333 |
| `post_failure_chain_recovery_steps` | 213.633 |
| `post_failure_chain_recovery_steps_censored` | 213.633 |
| `post_failure_chain_recovered_only_steps` | 0 |
| `chain_closed_during_failure_rate` | 0.00111111 |
| `tracking_during_failure_rate` | 0.174583 |
| `connectivity_during_failure` | 0.246389 |
| `avg_mean_range` | 17925.8 |
| `episode_min_blue_red_distance` | 1400.89 |
| `episode_min_blue_blue_distance` | 327.141 |
| `final_min_blue_red_distance` | 16451.6 |
| `final_min_blue_blue_distance` | 12931.4 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
