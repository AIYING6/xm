# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T10:55:10

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_no_graph_source_curriculum/runs/no_graph/bc_ppo_seed0/actor_critic_best.pt
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
| `success` | 0.38 |
| `chain_closed` | 0.38 |
| `attack_window_formed` | 0.88 |
| `attack_window_rate` | 0.0126091 |
| `tracking_rate` | 0.171263 |
| `comm_connectivity` | 0.458593 |
| `mean_message_age` | 69.3977 |
| `collision` | 0 |
| `timeout` | 0.62 |
| `constraint_violation` | 0 |
| `steps` | 178.4 |
| `first_attack_window_step` | 36.88 |
| `first_chain_close_step` | 16.58 |
| `post_failure_chain_recovered` | 0.38 |
| `post_failure_chain_recovery_steps` | 138.4 |
| `chain_closed_during_failure_rate` | 0.0621429 |
| `tracking_during_failure_rate` | 0.308917 |
| `connectivity_during_failure` | 0.211845 |
| `avg_mean_range` | 18879.7 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
