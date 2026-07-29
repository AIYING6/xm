# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T04:07:35

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
| `success` | 0.0333333 |
| `chain_closed` | 0.0333333 |
| `attack_window_formed` | 0.0333333 |
| `attack_window_rate` | 0.000683761 |
| `tracking_rate` | 0.188248 |
| `comm_connectivity` | 0.172479 |
| `mean_message_age` | 87.1251 |
| `collision` | 0 |
| `timeout` | 0.966667 |
| `constraint_violation` | 0 |
| `steps` | 253.5 |
| `first_attack_window_step` | 1.1 |
| `first_chain_close_step` | 1.2 |
| `post_failure_chain_recovered` | 0.0333333 |
| `post_failure_chain_recovery_steps` | 213.5 |
| `post_failure_chain_recovery_steps_censored` | 213.5 |
| `post_failure_chain_recovered_only_steps` | -0.133333 |
| `chain_closed_during_failure_rate` | 0.00128205 |
| `tracking_during_failure_rate` | 0.166207 |
| `connectivity_during_failure` | 0.163814 |
| `avg_mean_range` | 18242.5 |
| `episode_min_blue_red_distance` | 1667.61 |
| `episode_min_blue_blue_distance` | 642.502 |
| `final_min_blue_red_distance` | 15887 |
| `final_min_blue_blue_distance` | 15424.9 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
