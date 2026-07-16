# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T02:33:23

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_multirelation_bc_seed3/actor_critic_latest.pt
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
| `success` | 0.55 |
| `chain_closed` | 0.55 |
| `attack_window_formed` | 0.75 |
| `attack_window_rate` | 0.0168758 |
| `tracking_rate` | 0.283108 |
| `comm_connectivity` | 0.939744 |
| `mean_message_age` | 33.5127 |
| `collision` | 0 |
| `timeout` | 0.45 |
| `constraint_violation` | 0 |
| `steps` | 141.85 |
| `avg_mean_range` | 25562.5 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
