# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:08:01

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed1/mappo/actor_critic_update_0040.pt
episodes = 50
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
| `success` | 0.34 |
| `chain_closed` | 0.34 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.010218 |
| `tracking_rate` | 0.206365 |
| `comm_connectivity` | 0.447231 |
| `mean_message_age` | 55.7405 |
| `collision` | 0 |
| `timeout` | 0.66 |
| `constraint_violation` | 0 |
| `steps` | 186.92 |
| `first_attack_window_step` | 16.34 |
| `first_chain_close_step` | 14.66 |
| `post_failure_chain_recovered` | 0.34 |
| `post_failure_chain_recovery_steps` | 161.92 |
| `post_failure_chain_recovery_steps_censored` | 161.92 |
| `post_failure_chain_recovered_only_steps` | 6.16 |
| `chain_closed_during_failure_rate` | 0.0161688 |
| `tracking_during_failure_rate` | 0.446762 |
| `connectivity_during_failure` | 0.0984167 |
| `avg_mean_range` | 30883.3 |
| `episode_min_blue_red_distance` | 1861.86 |
| `episode_min_blue_blue_distance` | 4049.43 |
| `final_min_blue_red_distance` | 54203.1 |
| `final_min_blue_blue_distance` | 4745.62 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
