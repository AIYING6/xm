# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-28T04:55:49

```text
split = validation
seeds = [0]
scenarios = ['dropout030_delay2_relay_failure']
episodes = 2
base_seed = 140000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| dropout030_delay2_relay_failure | 0 | 100 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0100.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 1