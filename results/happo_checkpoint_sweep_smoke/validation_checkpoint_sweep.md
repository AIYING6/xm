# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-24T02:28:55

```text
split = validation
seeds = [0]
scenarios = ['relay_failure']
episodes = 1
base_seed = 120000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 0 | 1 | 0 | inf | 0 | `results/paper_config_runs/smoke/runs/happo/bc_ppo_seed0/happo_update_0001.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 1