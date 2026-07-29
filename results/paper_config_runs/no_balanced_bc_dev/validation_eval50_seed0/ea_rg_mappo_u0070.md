# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:17:29

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/ea_rg_mappo/actor_critic_update_0070.pt
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
| `success` | 0.28 |
| `chain_closed` | 0.28 |
| `attack_window_formed` | 0.38 |
| `attack_window_rate` | 0.00760432 |
| `tracking_rate` | 0.19295 |
| `comm_connectivity` | 0.493767 |
| `mean_message_age` | 50.6634 |
| `collision` | 0 |
| `timeout` | 0.72 |
| `constraint_violation` | 0 |
| `steps` | 201.48 |
| `first_attack_window_step` | 17.86 |
| `first_chain_close_step` | 13.56 |
| `post_failure_chain_recovered` | 0.28 |
| `post_failure_chain_recovery_steps` | 176.48 |
| `post_failure_chain_recovery_steps_censored` | 176.48 |
| `post_failure_chain_recovered_only_steps` | 6.56 |
| `chain_closed_during_failure_rate` | 0.0103805 |
| `tracking_during_failure_rate` | 0.407279 |
| `connectivity_during_failure` | 0.0769583 |
| `avg_mean_range` | 30797.1 |
| `episode_min_blue_red_distance` | 1734.7 |
| `episode_min_blue_blue_distance` | 2483.57 |
| `final_min_blue_red_distance` | 59943.7 |
| `final_min_blue_blue_distance` | 2483.57 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
