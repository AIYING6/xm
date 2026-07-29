# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-29T18:59:32

```text
split = validation
seeds = [0, 1, 2]
scenarios = ['dropout030_delay2_relay_failure_early', 'dropout030_delay2_relay_failure', 'dropout030_delay2_relay_failure_delayed', 'dropout030_delay2_relay_failure_late']
episodes = 10
base_seed = 291000
checkpoint_updates = [20, 30, 40]
selection_group = suite
selection_metric = delayed_recovery
delayed_recovery_min_step = 80
selection_success_weight = 0.0
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| scenario_suite | 0 | 20 | 0.475 | 79.15 | 0.425 | `results/paper_config_runs/stability_dev/happo_strong_offset_balanced_recovery_bc_safety05/ppo_seed0/happo_update_0020.pt` |
| scenario_suite | 1 | 40 | 0.2 | inf | 0.075 | `results/paper_config_runs/stability_dev/happo_strong_offset_balanced_recovery_bc_safety05/ppo_seed1/happo_update_0040.pt` |
| scenario_suite | 2 | 40 | 0.1 | inf | 0 | `results/paper_config_runs/stability_dev/happo_strong_offset_balanced_recovery_bc_safety05/ppo_seed2/happo_update_0040.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 36