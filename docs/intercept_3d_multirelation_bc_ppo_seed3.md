# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T02:36:55

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_multirelation_bc_ppo_seed3/actor_critic_best.pt
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
| `success` | 0.333333 |
| `chain_closed` | 0.333333 |
| `attack_window_formed` | 0.666667 |
| `attack_window_rate` | 0.0105634 |
| `tracking_rate` | 0.207363 |
| `comm_connectivity` | 0.98141 |
| `mean_message_age` | 30.8247 |
| `collision` | 0 |
| `timeout` | 0.666667 |
| `constraint_violation` | 0 |
| `steps` | 188.267 |
| `avg_mean_range` | 30800.2 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
