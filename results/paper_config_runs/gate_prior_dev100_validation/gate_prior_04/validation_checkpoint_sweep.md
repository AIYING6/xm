# 3DOF Strict-Sensing Checkpoint Sweep

Generated: 2026-07-28T18:55:37

Purpose:

```text
Evaluate checkpoint snapshots on a fixed matched split and select checkpoints before final testing.
Selection score = 1000 * recovery_rate + 100 * success_rate - mean_recovery_steps.
Final test evaluation should use the selected validation checkpoints and a disjoint base seed.
```

## Protocol

```text
split = validation
seeds = [0, 1, 2]
graph_encoders = ['multi_relation']
scenarios = ['dropout030_delay2_relay_failure']
episodes = 30
base_seed = 20000
strict_target_sensing = True
agent_target_info_bottleneck = True
target_prior_position = (10000.0, 0.0, 5000.0)
max_target_message_age_steps = 80
min_target_confidence = 0.2
selection_csv = none
max_selection_collision_rate = None
```

## Selected Checkpoints

| Scenario | Graph | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| dropout030_delay2_relay_failure | multi_relation | 0 | 60 | 0.133333 | 24.25 | 0.133333 | `results/paper_config_runs/gate_prior_dev100/runs/ea_rg_mappo_gate_prior/bc_ppo_seed0/actor_critic_update_0060.pt` |
| dropout030_delay2_relay_failure | multi_relation | 1 | 40 | 0.133333 | 22 | 0.133333 | `results/paper_config_runs/gate_prior_dev100/runs/ea_rg_mappo_gate_prior/bc_ppo_seed1/actor_critic_update_0040.pt` |
| dropout030_delay2_relay_failure | multi_relation | 2 | 100 | 0 | inf | 0 | `results/paper_config_runs/gate_prior_dev100/runs/ea_rg_mappo_gate_prior/bc_ppo_seed2/actor_critic_update_0100.pt` |

## Boundary

- Use validation split only for checkpoint selection and hyperparameter decisions.
- Use test split only after checkpoint selection is frozen.
- Do not compare test results from checkpoints selected on test episodes.

## Files

- Summary rows: `results/paper_config_runs/gate_prior_dev100_validation/gate_prior_04/validation_checkpoint_summary.csv`
- Episode rows: `results/paper_config_runs/gate_prior_dev100_validation/gate_prior_04/validation_episode_metrics.csv`
- Selected checkpoints: `results/paper_config_runs/gate_prior_dev100_validation/gate_prior_04/validation_selected_checkpoints.csv`

Evaluated checkpoint-scenario combinations: 15