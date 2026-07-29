# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-29T12:29:29

```text
split = validation
seeds = [0, 1, 2]
scenarios = ['dropout030_delay2_relay_failure_early', 'dropout030_delay2_relay_failure', 'dropout030_delay2_relay_failure_delayed', 'dropout030_delay2_relay_failure_late']
episodes = 5
base_seed = 290000
checkpoint_updates = [2200, 3800, 3907]
selection_group = suite
selection_metric = legacy_recovery
delayed_recovery_min_step = 80
selection_success_weight = 100.0
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| scenario_suite | 0 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_3907.pt` |
| scenario_suite | 1 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_3907.pt` |
| scenario_suite | 2 | 3907 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_3907.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 36