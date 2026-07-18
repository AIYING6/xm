# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T10:55:51

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed1/actor_critic_best.pt
episodes = 50
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.0
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
| `success` | 0.88 |
| `chain_closed` | 0.88 |
| `attack_window_formed` | 0.98 |
| `attack_window_rate` | 0.0260803 |
| `tracking_rate` | 0.287549 |
| `comm_connectivity` | 0.829964 |
| `mean_message_age` | 36.4639 |
| `collision` | 0 |
| `timeout` | 0.12 |
| `constraint_violation` | 0 |
| `steps` | 71.26 |
| `first_attack_window_step` | 41.68 |
| `first_chain_close_step` | 39.94 |
| `post_failure_chain_recovered` | 0.88 |
| `post_failure_chain_recovery_steps` | 31.26 |
| `chain_closed_during_failure_rate` | 0.140683 |
| `tracking_during_failure_rate` | 0.520825 |
| `connectivity_during_failure` | 0.395455 |
| `avg_mean_range` | 16169.2 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
