# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T04:06:36

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/ea_rg_mappo/bc_ppo_seed0/actor_critic_update_1600.pt
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
| `success` | 0.2 |
| `chain_closed` | 0.2 |
| `attack_window_formed` | 0.266667 |
| `attack_window_rate` | 0.00467657 |
| `tracking_rate` | 0.208834 |
| `comm_connectivity` | 0.307247 |
| `mean_message_age` | 62.5589 |
| `collision` | 0 |
| `timeout` | 0.8 |
| `constraint_violation` | 0 |
| `steps` | 220.067 |
| `first_attack_window_step` | 14.5333 |
| `first_chain_close_step` | 11.2667 |
| `post_failure_chain_recovered` | 0.2 |
| `post_failure_chain_recovery_steps` | 180.067 |
| `post_failure_chain_recovery_steps_censored` | 180.067 |
| `post_failure_chain_recovered_only_steps` | 3.26667 |
| `chain_closed_during_failure_rate` | 0.00937951 |
| `tracking_during_failure_rate` | 0.228389 |
| `connectivity_during_failure` | 0.197816 |
| `avg_mean_range` | 15291.1 |
| `episode_min_blue_red_distance` | 1957.87 |
| `episode_min_blue_blue_distance` | 2031.09 |
| `final_min_blue_red_distance` | 21577.8 |
| `final_min_blue_blue_distance` | 5185.9 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
