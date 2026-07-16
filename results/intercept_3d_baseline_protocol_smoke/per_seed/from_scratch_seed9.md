# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T01:57:36

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_baseline_protocol_smoke/runs/from_scratch_seed9/actor_critic_best.pt
episodes = 2
target_policy = straight
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.5 |
| `chain_closed` | 0.5 |
| `attack_window_formed` | 0.5 |
| `attack_window_rate` | 0.00584795 |
| `tracking_rate` | 0.0987854 |
| `comm_connectivity` | 0.812179 |
| `mean_message_age` | 50.6375 |
| `collision` | 0 |
| `timeout` | 0.5 |
| `constraint_violation` | 0 |
| `steps` | 187 |
| `avg_mean_range` | 15166 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
