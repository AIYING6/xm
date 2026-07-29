# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:26:46

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
| `success` | 0.933333 |
| `chain_closed` | 0.933333 |
| `attack_window_formed` | 0.933333 |
| `attack_window_rate` | 0.0212914 |
| `tracking_rate` | 0.325165 |
| `comm_connectivity` | 0.746636 |
| `mean_message_age` | 42.4495 |
| `collision` | 0 |
| `timeout` | 0.0666667 |
| `constraint_violation` | 0 |
| `steps` | 72 |
| `first_attack_window_step` | 51.8 |
| `first_chain_close_step` | 54.6 |
| `post_failure_chain_recovered` | 0.933333 |
| `post_failure_chain_recovery_steps` | 32 |
| `post_failure_chain_recovery_steps_censored` | 32 |
| `post_failure_chain_recovered_only_steps` | 17.2667 |
| `chain_closed_during_failure_rate` | 0.0485883 |
| `tracking_during_failure_rate` | 0.571273 |
| `connectivity_during_failure` | 0.333333 |
| `avg_mean_range` | 14973 |
| `episode_min_blue_red_distance` | 4160.25 |
| `episode_min_blue_blue_distance` | 4081.25 |
| `final_min_blue_red_distance` | 5715.72 |
| `final_min_blue_blue_distance` | 5321.4 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
