# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T11:54:07

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_strict_sensing_fair_30update_diag/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0015.pt
episodes = 20
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.0
message_delay_steps = 0
radar_dropout_prob = 0.1
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 1 |
| `chain_closed` | 1 |
| `attack_window_formed` | 1 |
| `attack_window_rate` | 0.0291398 |
| `tracking_rate` | 0.401793 |
| `comm_connectivity` | 0.908882 |
| `mean_message_age` | 54.2446 |
| `collision` | 0 |
| `timeout` | 0 |
| `constraint_violation` | 0 |
| `steps` | 46.4 |
| `first_attack_window_step` | 43.35 |
| `first_chain_close_step` | 46.4 |
| `post_failure_chain_recovered` | 1 |
| `post_failure_chain_recovery_steps` | 6.4 |
| `chain_closed_during_failure_rate` | 0.143494 |
| `tracking_during_failure_rate` | 0.887842 |
| `connectivity_during_failure` | 0.428996 |
| `avg_mean_range` | 14648.6 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
