# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-08-12T14:29:39

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/canonical_v2/smoke/no_union_residual/seed0/actor_critic_latest.pt
episodes = 1
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.3
message_delay_steps = 2
radar_dropout_prob = 0.0
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
multi_relation_global_residual_weight = 0.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0 |
| `chain_closed` | 0 |
| `attack_window_formed` | 0 |
| `attack_window_rate` | 0 |
| `tracking_rate` | 0.0346154 |
| `comm_connectivity` | 0.223718 |
| `mean_message_age` | 86.7936 |
| `collision` | 0 |
| `timeout` | 1 |
| `constraint_violation` | 0 |
| `steps` | 260 |
| `first_attack_window_step` | -1 |
| `first_chain_close_step` | -1 |
| `post_failure_chain_recovered` | 0 |
| `post_failure_chain_recovery_steps` | 220 |
| `post_failure_chain_recovery_steps_censored` | 220 |
| `post_failure_chain_recovered_only_steps` | -1 |
| `post_failure_fresh_info_recovered` | 0 |
| `post_failure_fresh_info_recovery_steps` | -1 |
| `post_failure_fresh_info_acquired_without_prior_loss` | 0 |
| `post_failure_fresh_direct_recovered` | 0 |
| `post_failure_fresh_comm_recovered` | 0 |
| `post_failure_post_delivered_old_info_recovered` | 0 |
| `post_failure_stale_cache_recovered` | 0 |
| `chain_closed_during_failure_rate` | 0 |
| `tracking_during_failure_rate` | 0.0208333 |
| `connectivity_during_failure` | 0.0645833 |
| `avg_mean_range` | 16493.6 |
| `episode_min_blue_red_distance` | 1272.53 |
| `episode_min_blue_blue_distance` | 1040.59 |
| `final_min_blue_red_distance` | 32095.8 |
| `final_min_blue_blue_distance` | 1040.59 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
