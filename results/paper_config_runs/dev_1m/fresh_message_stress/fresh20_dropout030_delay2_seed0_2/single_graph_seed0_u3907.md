# 3DOF RI-GMAPPO Policy Evaluation

Generated: 2026-07-29T04:07:59

Purpose:

```text
Evaluate a saved 3DOF EA-RG-MAPPO-S checkpoint with task-chain metrics.
This is a diagnostic artifact until multi-seed 3DOF training is completed.
```

## Configuration

```text
checkpoint = results/paper_config_runs/dev_1m/runs/single_graph/bc_ppo_seed0/actor_critic_update_3907.pt
episodes = 30
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
multi_relation_global_residual_weight = 1.0
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0.233333 |
| `chain_closed` | 0.233333 |
| `attack_window_formed` | 0.233333 |
| `attack_window_rate` | 0.00497634 |
| `tracking_rate` | 0.243326 |
| `comm_connectivity` | 0.341094 |
| `mean_message_age` | 62.4994 |
| `collision` | 0.0666667 |
| `timeout` | 0.7 |
| `constraint_violation` | 0 |
| `steps` | 205.567 |
| `first_attack_window_step` | 13.1333 |
| `first_chain_close_step` | 13.8333 |
| `post_failure_chain_recovered` | 0.233333 |
| `post_failure_chain_recovery_steps` | 165.567 |
| `post_failure_chain_recovery_steps_censored` | 165.567 |
| `post_failure_chain_recovered_only_steps` | 4.5 |
| `chain_closed_during_failure_rate` | 0.00995779 |
| `tracking_during_failure_rate` | 0.417746 |
| `connectivity_during_failure` | 0.173259 |
| `avg_mean_range` | 17411.3 |
| `episode_min_blue_red_distance` | 2473.06 |
| `episode_min_blue_blue_distance` | 988.645 |
| `final_min_blue_red_distance` | 17053.6 |
| `final_min_blue_blue_distance` | 5552.05 |

## Boundary

```text
Do not use this smoke-scale 3DOF policy evaluation as a paper result.
Use it to verify that checkpoint loading, 3DOF rollouts, and task-chain metric logging remain intact.
```
