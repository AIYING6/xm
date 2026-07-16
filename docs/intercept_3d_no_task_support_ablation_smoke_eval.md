# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T13:27:53

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_no_task_support_ablation_smoke/actor_critic_best.pt
episodes = 3
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
graph_relation_ablation = no_task_support
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 1 |
| `chain_closed` | 1 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0296394 |
| `tracking_rate` | 0.434326 |
| `comm_connectivity` | 0.926121 |
| `mean_message_age` | 44.5084 |
| `collision` | 0 |
| `timeout` | 0 |
| `constraint_violation` | 0 |
| `steps` | 45 |
| `first_attack_window_step` | 42 |
| `first_chain_close_step` | 45 |
| `post_failure_chain_recovered` | 1 |
| `post_failure_chain_recovery_steps` | 5 |
| `chain_closed_during_failure_rate` | 0.169841 |
| `tracking_during_failure_rate` | 1 |
| `connectivity_during_failure` | 0.446561 |
| `avg_mean_range` | 14889.5 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
