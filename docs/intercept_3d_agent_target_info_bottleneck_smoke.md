# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T12:55:18

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_strict_sensing_fair_60update_dropout030_diag/runs/multi_relation/bc_ppo_seed0/actor_critic_update_0030.pt
episodes = 1
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.3
message_delay_steps = 0
radar_dropout_prob = 0.0
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
| `attack_window_rate` | 0.0266667 |
| `tracking_rate` | 0.473333 |
| `comm_connectivity` | 0.636667 |
| `mean_message_age` | 52.1833 |
| `collision` | 0 |
| `timeout` | 0 |
| `constraint_violation` | 0 |
| `steps` | 50 |
| `first_attack_window_step` | 47 |
| `first_chain_close_step` | 50 |
| `post_failure_chain_recovered` | 1 |
| `post_failure_chain_recovery_steps` | 10 |
| `chain_closed_during_failure_rate` | 0.0909091 |
| `tracking_during_failure_rate` | 1 |
| `connectivity_during_failure` | 0.212121 |
| `avg_mean_range` | 13946.7 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
