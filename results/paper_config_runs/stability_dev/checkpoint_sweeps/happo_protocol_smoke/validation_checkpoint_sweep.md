# 3DOF HAPPO Checkpoint Sweep

Generated: 2026-07-29T18:31:24

```text
split = validation
seeds = [0]
scenarios = ['dropout030_delay2_relay_failure_delayed']
episodes = 1
base_seed = 291000
checkpoint_updates = [1]
selection_group = suite
selection_metric = delayed_recovery
delayed_recovery_min_step = 80
selection_success_weight = 0.0
selection_csv = none
```

| Scenario | Seed | Update | Recovery | Recovery steps | Success | Checkpoint |
|---|---:|---:|---:|---:|---:|---|
| scenario_suite | 0 | 1 | 0 | inf | 0 | `results/paper_config_runs/stability_dev/happo_protocol_smoke_root/bc_ppo_seed0/happo_update_0001.pt` |

## Boundary

- HAPPO uses the same validation/test selection schema as the other paper methods.
- Test split should use validation-selected checkpoints through `--selection-csv`.

Evaluated checkpoint-scenario combinations: 1