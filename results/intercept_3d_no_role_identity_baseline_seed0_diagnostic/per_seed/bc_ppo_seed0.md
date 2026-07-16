# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-16T17:49:37

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_no_role_identity_baseline_seed0_diagnostic/runs/bc_ppo_seed0/actor_critic_best.pt
episodes = 30
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
graph_input_ablation = no_role_identity
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.9 |
| `chain_closed` | 0.9 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0262208 |
| `tracking_rate` | 0.41291 |
| `comm_connectivity` | 0.957051 |
| `mean_message_age` | 43.0272 |
| `collision` | 0 |
| `timeout` | 0.1 |
| `constraint_violation` | 0 |
| `steps` | 67.5667 |
| `first_attack_window_step` | 43.5333 |
| `first_chain_close_step` | 41.4667 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 16987.8 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
