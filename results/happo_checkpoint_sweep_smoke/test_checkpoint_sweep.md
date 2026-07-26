# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-24T02:29:00

```text
split = test
seeds = [0]
scenarios = ['relay_failure']
episodes = 1
base_seed = 130000
selection_csv = results/happo_checkpoint_sweep_smoke/validation_selected_checkpoints.csv
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| relay_failure | 0 | 1 | 0 | inf | 0 | `results/paper_config_runs/smoke/runs/happo/bc_ppo_seed0/happo_update_0001.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 1