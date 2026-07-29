# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-28T06:59:14

```text
split = validation
seeds = [0, 1, 2]
scenarios = ['dropout030_delay2_relay_failure']
episodes = 50
base_seed = 140000
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| dropout030_delay2_relay_failure | 0 | 900 | 0.26 | 80.3846 | 0.26 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0900.pt` |
| dropout030_delay2_relay_failure | 1 | 3300 | 0.02 | 80 | 0.02 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_3300.pt` |
| dropout030_delay2_relay_failure | 2 | 2300 | 0.28 | 114.143 | 0.28 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_2300.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 140