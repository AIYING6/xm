# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T04:07:03

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
| `success` | 0.433333 |
| `chain_closed` | 0.433333 |
| `attack_window_formed` | 0.6 |
| `attack_window_rate` | 0.00949561 |
| `tracking_rate` | 0.284529 |
| `comm_connectivity` | 0.342125 |
| `mean_message_age` | 58.2597 |
| `collision` | 0 |
| `timeout` | 0.566667 |
| `constraint_violation` | 0 |
| `steps` | 188.733 |
| `first_attack_window_step` | 36.8 |
| `first_chain_close_step` | 40.8333 |
| `post_failure_chain_recovered` | 0.433333 |
| `post_failure_chain_recovery_steps` | 148.733 |
| `post_failure_chain_recovery_steps_censored` | 148.733 |
| `post_failure_chain_recovered_only_steps` | 23.5 |
| `chain_closed_during_failure_rate` | 0.0240652 |
| `tracking_during_failure_rate` | 0.474025 |
| `connectivity_during_failure` | 0.199851 |
| `avg_mean_range` | 14962.1 |
| `episode_min_blue_red_distance` | 2481.13 |
| `episode_min_blue_blue_distance` | 2019.29 |
| `final_min_blue_red_distance` | 8764.25 |
| `final_min_blue_blue_distance` | 8611.6 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
