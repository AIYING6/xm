# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T01:49:22

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_bc_ppo_straight_60/actor_critic_best.pt
episodes = 20
target_policy = straight
communication_dropout_prob = 0.15
message_delay_steps = 2
radar_dropout_prob = 0.1
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 1 |
| `chain_closed` | 1 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0291145 |
| `tracking_rate` | 0.395977 |
| `comm_connectivity` | 0.897652 |
| `mean_message_age` | 38.5803 |
| `collision` | 0 |
| `timeout` | 0 |
| `constraint_violation` | 0 |
| `steps` | 45.85 |
| `avg_mean_range` | 14684.7 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
