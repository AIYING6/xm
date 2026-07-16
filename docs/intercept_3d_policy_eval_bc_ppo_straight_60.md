# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T01:49:14

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_bc_ppo_straight_60/actor_critic_best.pt
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
| `success` | 0.966667 |
| `chain_closed` | 0.966667 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0283495 |
| `tracking_rate` | 0.428857 |
| `comm_connectivity` | 0.986795 |
| `mean_message_age` | 41.578 |
| `collision` | 0 |
| `timeout` | 0.0333333 |
| `constraint_violation` | 0 |
| `steps` | 52.8 |
| `avg_mean_range` | 15496.8 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
