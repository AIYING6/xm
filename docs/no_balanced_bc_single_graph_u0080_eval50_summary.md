# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:53:37

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/single_graph/actor_critic_update_0080.pt
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
| `success` | 0.4 |
| `chain_closed` | 0.4 |
| `attack_window_formed` | 0.72 |
| `attack_window_rate` | 0.0126131 |
| `tracking_rate` | 0.222403 |
| `comm_connectivity` | 0.29837 |
| `mean_message_age` | 64.4936 |
| `collision` | 0 |
| `timeout` | 0.6 |
| `constraint_violation` | 0 |
| `steps` | 173.94 |
| `first_attack_window_step` | 30.68 |
| `first_chain_close_step` | 17.34 |
| `post_failure_chain_recovered` | 0.4 |
| `post_failure_chain_recovery_steps` | 148.94 |
| `post_failure_chain_recovery_steps_censored` | 148.94 |
| `post_failure_chain_recovered_only_steps` | 7.34 |
| `chain_closed_during_failure_rate` | 0.0192121 |
| `tracking_during_failure_rate` | 0.471299 |
| `connectivity_during_failure` | 0.169117 |
| `avg_mean_range` | 28638.7 |
| `episode_min_blue_red_distance` | 2191.99 |
| `episode_min_blue_blue_distance` | 2610.24 |
| `final_min_blue_red_distance` | 46652.3 |
| `final_min_blue_blue_distance` | 6391.89 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
