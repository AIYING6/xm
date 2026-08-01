# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-08-02T01:40:44

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/ri_gmappo_3d_smoke/actor_critic_latest.pt
episodes = 3
target_policy = evasive
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
multi_relation_global_residual_weight = 1.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0 |
| `chain_closed` | 0 |
| `attack_window_formed` | 0 |
| `attack_window_rate` | 0 |
| `tracking_rate` | 0.0290598 |
| `comm_connectivity` | 0.62265 |
| `mean_message_age` | 66.8919 |
| `collision` | 0 |
| `timeout` | 1 |
| `constraint_violation` | 0 |
| `steps` | 260 |
| `first_attack_window_step` | -1 |
| `first_chain_close_step` | -1 |
| `post_failure_chain_recovered` | -1 |
| `post_failure_chain_recovery_steps` | -1 |
| `post_failure_chain_recovery_steps_censored` | -1 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `post_failure_fresh_info_recovered` | -1 |
| `post_failure_fresh_info_recovery_steps` | -1 |
| `post_failure_fresh_info_acquired_without_prior_loss` | -1 |
| `post_failure_fresh_direct_recovered` | -1 |
| `post_failure_fresh_comm_recovered` | -1 |
| `post_failure_post_delivered_old_info_recovered` | -1 |
| `post_failure_stale_cache_recovered` | -1 |
| `chain_closed_during_failure_rate` | -1 |
| `tracking_during_failure_rate` | -1 |
| `connectivity_during_failure` | -1 |
| `avg_mean_range` | 39355.6 |
| `episode_min_blue_red_distance` | 15811.3 |
| `episode_min_blue_blue_distance` | 3443.7 |
| `final_min_blue_red_distance` | 49647.2 |
| `final_min_blue_blue_distance` | 6489.79 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
