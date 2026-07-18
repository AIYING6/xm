# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-17T11:49:57

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_strict_sensing_fair_30update_diag/runs/no_graph/bc_ppo_seed0/actor_critic_update_0020.pt
episodes = 20
target_policy = straight
communication_range_scale = 0.75
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
| `success` | 0.25 |
| `chain_closed` | 0.25 |
| `attack_window_formed` | 0.8 |
| `attack_window_rate` | 0.00885604 |
| `tracking_rate` | 0.135553 |
| `comm_connectivity` | 0.362377 |
| `mean_message_age` | 85.8381 |
| `collision` | 0 |
| `timeout` | 0.75 |
| `constraint_violation` | 0 |
| `steps` | 206.1 |
| `first_attack_window_step` | 33.5 |
| `first_chain_close_step` | 10.35 |
| `post_failure_chain_recovered` | 0.25 |
| `post_failure_chain_recovery_steps` | 166.1 |
| `chain_closed_during_failure_rate` | 0.0471429 |
| `tracking_during_failure_rate` | 0.225417 |
| `connectivity_during_failure` | 0.152679 |
| `avg_mean_range` | 20198.4 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
