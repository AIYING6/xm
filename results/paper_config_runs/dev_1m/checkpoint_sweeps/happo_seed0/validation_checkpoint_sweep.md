# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-27T00:45:50

```text
split = validation
seeds = [0]
scenarios = ['relay_failure']
episodes = 50
base_seed = 120000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 0 | 900 | 0.14 | 81.2857 | 0.14 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0900.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 40