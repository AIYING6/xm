# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T01:22:35

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_seed0/mappo/actor_critic_latest.pt
episodes = 30
target_policy = straight
communication_range_scale = 1.0
communication_dropout_prob = 0.3
message_delay_steps = 2
radar_dropout_prob = 0.0
failed_blue_agent = 1
node_failure_start_step = 25
node_failure_duration_steps = 80
graph_relation_ablation = none
graph_message_ablation = none
graph_input_ablation = none
multi_relation_global_residual_weight = 1.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.4 |
| `chain_closed` | 0.4 |
| `attack_window_formed` | 0.466667 |
| `attack_window_rate` | 0.011983 |
| `tracking_rate` | 0.223272 |
| `comm_connectivity` | 0.438148 |
| `mean_message_age` | 58.8224 |
| `collision` | 0 |
| `timeout` | 0.6 |
| `constraint_violation` | 0 |
| `steps` | 174 |
| `first_attack_window_step` | 19.2 |
| `first_chain_close_step` | 17.4 |
| `post_failure_chain_recovered` | 0.4 |
| `post_failure_chain_recovery_steps` | 149 |
| `post_failure_chain_recovery_steps_censored` | 149 |
| `post_failure_chain_recovered_only_steps` | 7.4 |
| `chain_closed_during_failure_rate` | 0.0190693 |
| `tracking_during_failure_rate` | 0.471919 |
| `connectivity_during_failure` | 0.0886806 |
| `avg_mean_range` | 29463.5 |
| `episode_min_blue_red_distance` | 2049.79 |
| `episode_min_blue_blue_distance` | 4065 |
| `final_min_blue_red_distance` | 49362.5 |
| `final_min_blue_blue_distance` | 4679.96 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
