# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-27T18:52:23

```text
split = validation
seeds = [1, 2]
scenarios = ['relay_failure']
episodes = 50
base_seed = 120000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 1 | 2900 | 0.2 | 88.2 | 0.2 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_2900.pt` |
| relay_failure | 2 | 2100 | 0.02 | 70 | 0.02 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_2100.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 100