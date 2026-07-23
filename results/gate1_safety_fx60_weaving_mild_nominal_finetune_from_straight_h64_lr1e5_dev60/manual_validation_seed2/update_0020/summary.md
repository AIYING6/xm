# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-22T14:24:20

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/gate1_safety_fx60_weaving_mild_nominal_finetune_from_straight_h64_lr1e5_dev60/runs/multi_relation/bc_ppo_seed2/actor_critic_update_0020.pt
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
| `success` | 0.2 |
| `chain_closed` | 0.2 |
| `attack_window_formed` | 0.2 |
| `attack_window_rate` | 0.00189588 |
| `tracking_rate` | 0.21563 |
| `comm_connectivity` | 0.3718 |
| `mean_message_age` | 58.8784 |
| `collision` | 0 |
| `timeout` | 0.8 |
| `constraint_violation` | 0 |
| `steps` | 245.033 |
| `first_attack_window_step` | 35.4 |
| `first_chain_close_step` | 36.2333 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 22759.5 |
| `episode_min_blue_red_distance` | 6374.54 |
| `episode_min_blue_blue_distance` | 577.251 |
| `final_min_blue_red_distance` | 14493.4 |
| `final_min_blue_blue_distance` | 16270.8 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
