# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T02:06:07

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_seed1/ea_rg_mappo/actor_critic_latest.pt
episodes = 30
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
| `success` | 0.4 |
| `chain_closed` | 0.4 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.0120931 |
| `tracking_rate` | 0.224003 |
| `comm_connectivity` | 0.430195 |
| `mean_message_age` | 62.0622 |
| `collision` | 0 |
| `timeout` | 0.6 |
| `constraint_violation` | 0 |
| `steps` | 173.9 |
| `first_attack_window_step` | 19.1 |
| `first_chain_close_step` | 17.3 |
| `post_failure_chain_recovered` | 0.4 |
| `post_failure_chain_recovery_steps` | 148.9 |
| `post_failure_chain_recovery_steps_censored` | 148.9 |
| `post_failure_chain_recovered_only_steps` | 7.3 |
| `chain_closed_during_failure_rate` | 0.0193074 |
| `tracking_during_failure_rate` | 0.474541 |
| `connectivity_during_failure` | 0.0915972 |
| `avg_mean_range` | 29464.1 |
| `episode_min_blue_red_distance` | 2082.64 |
| `episode_min_blue_blue_distance` | 3751.16 |
| `final_min_blue_red_distance` | 49435.2 |
| `final_min_blue_blue_distance` | 5001.59 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
