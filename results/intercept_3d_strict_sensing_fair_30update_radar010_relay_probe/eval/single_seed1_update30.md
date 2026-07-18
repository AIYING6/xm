# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T11:55:23

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_strict_sensing_fair_30update_diag/runs/single/bc_ppo_seed1/actor_critic_update_0030.pt
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
| `success` | 0.95 |
| `chain_closed` | 0.95 |
| `attack_window_formed` | 0.95 |
| `attack_window_rate` | 0.0279117 |
| `tracking_rate` | 0.378236 |
| `comm_connectivity` | 0.903234 |
| `mean_message_age` | 43.5011 |
| `collision` | 0 |
| `timeout` | 0.05 |
| `constraint_violation` | 0 |
| `steps` | 56.15 |
| `first_attack_window_step` | 40.25 |
| `first_chain_close_step` | 43.1 |
| `post_failure_chain_recovered` | 0.95 |
| `post_failure_chain_recovery_steps` | 16.15 |
| `chain_closed_during_failure_rate` | 0.154603 |
| `tracking_during_failure_rate` | 0.842298 |
| `connectivity_during_failure` | 0.436819 |
| `avg_mean_range` | 15969.9 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
