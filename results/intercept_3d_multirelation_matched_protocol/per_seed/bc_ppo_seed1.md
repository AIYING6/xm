# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T10:59:58

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_multirelation_matched_protocol/runs/bc_ppo_seed1/actor_critic_best.pt
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
| `success` | 0.8 |
| `chain_closed` | 0.8 |
| `attack_window_formed` | 0.933333 |
| `attack_window_rate` | 0.0238683 |
| `tracking_rate` | 0.369533 |
| `comm_connectivity` | 0.925641 |
| `mean_message_age` | 47.7714 |
| `collision` | 0 |
| `timeout` | 0.2 |
| `constraint_violation` | 0 |
| `steps` | 88.3 |
| `avg_mean_range` | 19384.9 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
