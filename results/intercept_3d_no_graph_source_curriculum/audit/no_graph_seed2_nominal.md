# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T10:56:43

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed2/actor_critic_best.pt
episodes = 50
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
failed_blue_agent = -1
node_failure_start_step = 0
node_failure_duration_steps = 0
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.22 |
| `chain_closed` | 0.22 |
| `attack_window_formed` | 0.78 |
| `attack_window_rate` | 0.0078913 |
| `tracking_rate` | 0.0884744 |
| `comm_connectivity` | 0.458103 |
| `mean_message_age` | 62.2792 |
| `collision` | 0 |
| `timeout` | 0.78 |
| `constraint_violation` | 0 |
| `steps` | 212.76 |
| `first_attack_window_step` | 32.7 |
| `first_chain_close_step` | 9.18 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 18986.6 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
