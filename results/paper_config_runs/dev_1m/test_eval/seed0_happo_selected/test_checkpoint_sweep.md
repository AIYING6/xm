# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-27T01:05:21

```text
split = test
seeds = [0]
scenarios = ['relay_failure']
episodes = 100
base_seed = 220000
selection_csv = results/paper_config_runs/dev_1m/checkpoint_sweeps/happo_seed0/validation_selected_checkpoints.csv
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 0 | 900 | 0.08 | 79.875 | 0.08 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0900.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 1