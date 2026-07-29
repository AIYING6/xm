# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T02:08:38

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_seed2/mappo/actor_critic_latest.pt
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
| `attack_window_rate` | 0.0121133 |
| `tracking_rate` | 0.225542 |
| `comm_connectivity` | 0.435477 |
| `mean_message_age` | 59.1039 |
| `collision` | 0 |
| `timeout` | 0.6 |
| `constraint_violation` | 0 |
| `steps` | 173.933 |
| `first_attack_window_step` | 19.1333 |
| `first_chain_close_step` | 17.3333 |
| `post_failure_chain_recovered` | 0.4 |
| `post_failure_chain_recovery_steps` | 148.933 |
| `post_failure_chain_recovery_steps_censored` | 148.933 |
| `post_failure_chain_recovered_only_steps` | 7.33333 |
| `chain_closed_during_failure_rate` | 0.019228 |
| `tracking_during_failure_rate` | 0.478191 |
| `connectivity_during_failure` | 0.0915278 |
| `avg_mean_range` | 29467.8 |
| `episode_min_blue_red_distance` | 2031.67 |
| `episode_min_blue_blue_distance` | 4168.93 |
| `final_min_blue_red_distance` | 49590.2 |
| `final_min_blue_blue_distance` | 4574.26 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
