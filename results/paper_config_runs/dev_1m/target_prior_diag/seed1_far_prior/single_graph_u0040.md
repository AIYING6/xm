# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:39:05

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed1/actor_critic_update_0040.pt
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
| `attack_window_formed` | 0.166667 |
| `attack_window_rate` | 0.000886303 |
| `tracking_rate` | 0.0570017 |
| `comm_connectivity` | 0.387608 |
| `mean_message_age` | 62.2964 |
| `collision` | 0 |
| `timeout` | 0.966667 |
| `constraint_violation` | 0 |
| `steps` | 255.3 |
| `first_attack_window_step` | 18.7333 |
| `first_chain_close_step` | 3 |
| `post_failure_chain_recovered` | 0.0333333 |
| `post_failure_chain_recovery_steps` | 215.3 |
| `post_failure_chain_recovery_steps_censored` | 215.3 |
| `post_failure_chain_recovered_only_steps` | 1.66667 |
| `chain_closed_during_failure_rate` | 0.000416667 |
| `tracking_during_failure_rate` | 0.07 |
| `connectivity_during_failure` | 0.165 |
| `avg_mean_range` | 15119.1 |
| `episode_min_blue_red_distance` | 3930.48 |
| `episode_min_blue_blue_distance` | 1681.63 |
| `final_min_blue_red_distance` | 25849.1 |
| `final_min_blue_blue_distance` | 3296.51 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
