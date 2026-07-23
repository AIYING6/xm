# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:23:49

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev60/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0010.pt
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
| `success` | 0.266667 |
| `chain_closed` | 0.266667 |
| `attack_window_formed` | 0.266667 |
| `attack_window_rate` | 0.00195233 |
| `tracking_rate` | 0.228206 |
| `comm_connectivity` | 0.377592 |
| `mean_message_age` | 57.6224 |
| `collision` | 0 |
| `timeout` | 0.733333 |
| `constraint_violation` | 0 |
| `steps` | 240.867 |
| `first_attack_window_step` | 48.6667 |
| `first_chain_close_step` | 49.4667 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 22435.5 |
| `episode_min_blue_red_distance` | 6201.49 |
| `episode_min_blue_blue_distance` | 554.056 |
| `final_min_blue_red_distance` | 12319.6 |
| `final_min_blue_blue_distance` | 14985.6 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
