# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T03:16:06

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/no_balanced_bc_dev/bc_ppo_seed0/ea_rg_mappo/actor_critic_update_0030.pt
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
| `success` | 0.28 |
| `chain_closed` | 0.28 |
| `attack_window_formed` | 0.4 |
| `attack_window_rate` | 0.00871102 |
| `tracking_rate` | 0.185126 |
| `comm_connectivity` | 0.470999 |
| `mean_message_age` | 50.5918 |
| `collision` | 0 |
| `timeout` | 0.72 |
| `constraint_violation` | 0 |
| `steps` | 199.68 |
| `first_attack_window_step` | 16.26 |
| `first_chain_close_step` | 11.76 |
| `post_failure_chain_recovered` | 0.28 |
| `post_failure_chain_recovery_steps` | 174.68 |
| `post_failure_chain_recovery_steps_censored` | 174.68 |
| `post_failure_chain_recovered_only_steps` | 4.76 |
| `chain_closed_during_failure_rate` | 0.0136234 |
| `tracking_during_failure_rate` | 0.415817 |
| `connectivity_during_failure` | 0.109333 |
| `avg_mean_range` | 32298.1 |
| `episode_min_blue_red_distance` | 1701.32 |
| `episode_min_blue_blue_distance` | 3348.66 |
| `final_min_blue_red_distance` | 56512 |
| `final_min_blue_blue_distance` | 4720.37 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
