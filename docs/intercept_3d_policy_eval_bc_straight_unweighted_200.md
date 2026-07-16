# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T01:47:11

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_bc_straight_unweighted_200/actor_critic_latest.pt
episodes = 20
target_policy = straight
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.7 |
| `chain_closed` | 0.7 |
| `attack_window_formed` | 0.75 |
| `attack_window_rate` | 0.0206201 |
| `tracking_rate` | 0.335722 |
| `comm_connectivity` | 0.920705 |
| `mean_message_age` | 41.5398 |
| `collision` | 0 |
| `timeout` | 0.3 |
| `constraint_violation` | 0 |
| `steps` | 109.8 |
| `avg_mean_range` | 21985.2 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
