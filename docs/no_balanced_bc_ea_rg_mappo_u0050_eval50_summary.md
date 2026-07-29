# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:50:00

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/ea_rg_mappo/actor_critic_update_0050.pt
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
| `success` | 0.44 |
| `chain_closed` | 0.44 |
| `attack_window_formed` | 0.72 |
| `attack_window_rate` | 0.0136836 |
| `tracking_rate` | 0.240303 |
| `comm_connectivity` | 0.450574 |
| `mean_message_age` | 55.4163 |
| `collision` | 0 |
| `timeout` | 0.56 |
| `constraint_violation` | 0 |
| `steps` | 165.32 |
| `first_attack_window_step` | 30.54 |
| `first_chain_close_step` | 19.16 |
| `post_failure_chain_recovered` | 0.44 |
| `post_failure_chain_recovery_steps` | 140.32 |
| `post_failure_chain_recovery_steps_censored` | 140.32 |
| `post_failure_chain_recovered_only_steps` | 8.16 |
| `chain_closed_during_failure_rate` | 0.0211645 |
| `tracking_during_failure_rate` | 0.503217 |
| `connectivity_during_failure` | 0.121427 |
| `avg_mean_range` | 28382.6 |
| `episode_min_blue_red_distance` | 2192.97 |
| `episode_min_blue_blue_distance` | 4414.68 |
| `final_min_blue_red_distance` | 45492.3 |
| `final_min_blue_blue_distance` | 4863.81 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
