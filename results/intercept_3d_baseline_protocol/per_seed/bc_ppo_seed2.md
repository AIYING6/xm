# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T02:15:53

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_baseline_protocol/runs/bc_ppo_seed2/actor_critic_best.pt
episodes = 30
target_policy = straight
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.933333 |
| `chain_closed` | 0.933333 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0276521 |
| `tracking_rate` | 0.416621 |
| `comm_connectivity` | 0.966453 |
| `mean_message_age` | 43.9116 |
| `collision` | 0 |
| `timeout` | 0.0666667 |
| `constraint_violation` | 0 |
| `steps` | 59.7667 |
| `avg_mean_range` | 16125.6 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
