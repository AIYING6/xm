# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-27T22:31:09

```text
split = test
seeds = [1, 2]
scenarios = ['relay_failure']
episodes = 100
base_seed = 220000
selection_csv = results/paper_config_runs/dev_1m/checkpoint_sweeps/happo_seeds1_2/validation_selected_checkpoints.csv
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 1 | 2900 | 0.2 | 88.2 | 0.2 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_2900.pt` |
| relay_failure | 2 | 2100 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_2100.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 2