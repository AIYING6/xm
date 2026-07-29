# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-28T01:01:27

```text
split = validation
seeds = [0, 1, 2]
scenarios = ['dropout030_relay_failure']
episodes = 50
base_seed = 130000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| dropout030_relay_failure | 0 | 900 | 0.26 | 80 | 0.26 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0900.pt` |
| dropout030_relay_failure | 1 | 1000 | 0.04 | 71 | 0.04 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_1000.pt` |
| dropout030_relay_failure | 2 | 2400 | 0.12 | 105.167 | 0.12 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_2400.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 140