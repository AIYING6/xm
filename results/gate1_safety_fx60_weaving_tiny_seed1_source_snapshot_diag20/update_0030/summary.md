# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:43:42

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/runs/multi_relation/bc_ppo_seed1/actor_critic_update_0030.pt
episodes = 20
target_policy = weaving_tiny
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
| `success` | 0 |
| `chain_closed` | 0 |
| `attack_window_formed` | 0 |
| `attack_window_rate` | 0 |
| `tracking_rate` | 0.210027 |
| `comm_connectivity` | 0.401317 |
| `mean_message_age` | 58.2112 |
| `collision` | 0.05 |
| `timeout` | 0.95 |
| `constraint_violation` | 0 |
| `steps` | 257.35 |
| `first_attack_window_step` | -1 |
| `first_chain_close_step` | -1 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 23913 |
| `episode_min_blue_red_distance` | 9290.6 |
| `episode_min_blue_blue_distance` | 1162.34 |
| `final_min_blue_red_distance` | 23944.5 |
| `final_min_blue_blue_distance` | 15101.5 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
