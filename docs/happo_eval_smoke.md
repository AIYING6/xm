# 3DOF HAPPO Policy Evaluation

Generated: 2026-07-24T02:27:14

## Configuration

```text
checkpoint = results/paper_config_runs/smoke/runs/happo/bc_ppo_seed0/happo_update_0001.pt
episodes = 1
target_policy = straight
communication_dropout_prob = 0.3
failed_blue_agent = 1
node_failure_start_step = 40
node_failure_duration_steps = 80
deterministic = True
```

## Metric Means

| Metric | Mean |
|---|---:|
| `success` | 0 |
| `post_failure_chain_recovered` | 0 |
| `post_failure_chain_recovery_steps` | 220 |
| `chain_closed_during_failure_rate` | 0 |
| `tracking_during_failure_rate` | 0.158333 |
| `connectivity_during_failure` | 0.24375 |
| `collision` | 0 |
| `timeout` | 1 |
| `constraint_violation` | 0 |
| `steps` | 260 |
| `avg_mean_range` | 16388.5 |
| `episode_min_blue_red_distance` | 1660.37 |
| `episode_min_blue_blue_distance` | 2304.78 |

## Boundary

```text
This evaluates the no-graph HAPPO-style external baseline.
Use paper-facing claims only after checkpoint-sweep selection is connected.
```
