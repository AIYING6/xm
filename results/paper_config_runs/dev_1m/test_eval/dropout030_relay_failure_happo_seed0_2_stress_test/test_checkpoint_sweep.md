# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-27T22:51:54

```text
split = test
seeds = [0, 1, 2]
scenarios = ['dropout030_relay_failure']
episodes = 100
base_seed = 240000
selection_csv = results/paper_config_runs/dev_1m/checkpoint_sweeps/happo_seed0_2_validation_selected_for_stress_test.csv
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| dropout030_relay_failure | 0 | 900 | 0.32 | 80.4375 | 0.32 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed0/happo_update_0900.pt` |
| dropout030_relay_failure | 1 | 2900 | 0 | inf | 0 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1/happo_update_2900.pt` |
| dropout030_relay_failure | 2 | 2100 | 0.02 | 71 | 0.02 | `results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2/happo_update_2100.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 3