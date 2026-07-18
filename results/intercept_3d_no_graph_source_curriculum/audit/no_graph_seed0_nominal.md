# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T10:54:22

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
failed_blue_agent = -1
node_failure_start_step = 0
node_failure_duration_steps = 0
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.46 |
| `chain_closed` | 0.46 |
| `attack_window_formed` | 0.88 |
| `attack_window_rate` | 0.0139441 |
| `tracking_rate` | 0.18355 |
| `comm_connectivity` | 0.587485 |
| `mean_message_age` | 55.9308 |
| `collision` | 0.04 |
| `timeout` | 0.5 |
| `constraint_violation` | 0 |
| `steps` | 165.44 |
| `first_attack_window_step` | 36.88 |
| `first_chain_close_step` | 32.46 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 18198.3 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
