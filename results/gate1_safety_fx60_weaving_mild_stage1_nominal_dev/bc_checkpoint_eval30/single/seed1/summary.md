# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T13:24:01

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/gate1_safety_fx60_weaving_mild_stage1_nominal_dev/stage1_bc/single/seed1/actor_critic_best.pt
episodes = 30
target_policy = weaving_mild
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
| `success` | 0.433333 |
| `chain_closed` | 0.433333 |
| `attack_window_formed` | 0.433333 |
| `attack_window_rate` | 0.00309061 |
| `tracking_rate` | 0.44161 |
| `comm_connectivity` | 0.834499 |
| `mean_message_age` | 17.9771 |
| `collision` | 0 |
| `timeout` | 0.566667 |
| `constraint_violation` | 0 |
| `steps` | 228.6 |
| `first_attack_window_step` | 79.4 |
| `first_chain_close_step` | 80.7 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 13680.6 |
| `episode_min_blue_red_distance` | 6324.69 |
| `episode_min_blue_blue_distance` | 1058.7 |
| `final_min_blue_red_distance` | 7991.89 |
| `final_min_blue_blue_distance` | 4250.15 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
