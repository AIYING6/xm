# Role-Gate Prior Seed0 Dev100 Summary

Last updated: 2026-07-29

## Purpose

Previous role-graph diagnostics showed that the multi-relation role-pair gates
were almost neutral: mean absolute gate deviation from 0.5 was only about
`0.000154`. This weakened the mechanism claim for EA-RG-MAPPO because the model
was not clearly using role-pair-conditioned message passing.

This diagnostic tests a lightweight role-gate prior with strength `0.4`.

## Protocol

- Method: EA-RG-MAPPO + role-gate prior.
- `role_gate_prior_strength=0.4`.
- Seed: 0.
- BC: 120 balanced offset geometric demonstration episodes, 20 epochs.
- PPO: 100 updates.
- Checkpoint candidates: 20, 40, 60, 80, 100.
- Validation scenarios:
  - `dropout030_delay2_relay_failure_early`
  - `dropout030_delay2_relay_failure`
  - `dropout030_delay2_relay_failure_delayed`
  - `dropout030_delay2_relay_failure_late`
- Selection: suite-level delayed recovery with `delayed_recovery_min_step=80`
  and success weight `0`.

Outputs:

- Training root:
  `results/paper_config_runs/stability_dev/ea_rg_mappo_role_gate_prior_strong_offset_balanced_recovery_bc_safety05/`
- Sweep root:
  `results/paper_config_runs/stability_dev/checkpoint_sweeps/ea_rg_mappo_role_gate_prior_strong_offset_balanced_recovery_bc_safety05_seed0_dev100/`
- Diagnostics:
  `results/paper_config_runs/stability_dev/role_graph_diagnostics/ea_rg_mappo_role_gate_prior_seed0_update60/`

## Result

Suite-level checkpoint selection chose update 60.

| Method / seed | Update | Success | Post-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|---:|
| Original EA seed0 | 30 | 0.575 | 0.725 | 0.275 | 0.000 |
| Role-gate prior seed0 | 60 | 0.925 | 0.950 | 0.525 | 0.000 |

Scenario-level update-60 validation:

| Scenario | Success | Post-loss recovery | Delayed recovery | Collision |
|---|---:|---:|---:|---:|
| Early | 0.700 | 0.800 | 0.000 | 0.000 |
| Standard | 1.000 | 1.000 | 0.100 | 0.000 |
| Delayed | 1.000 | 1.000 | 1.000 | 0.000 |
| Late | 1.000 | 1.000 | 1.000 | 0.000 |

## Mechanism Diagnostic

Role-pair gate diagnostics on the selected update-60 checkpoint:

- Mean absolute gate deviation from 0.5: `0.025573`.
- Max absolute gate deviation from 0.5: `0.121487`.

This is much larger than the previous near-neutral gate deviation
(`~0.000154`), so the prior appears to make the role-pair gates meaningfully
non-neutral.

## Interpretation

This is the strongest single-seed result so far for the EA multi-relation line.
It suggests the role-gate prior may solve two problems at once:

1. Improve the seed0 performance gap against the original EA checkpoint.
2. Strengthen the method's mechanism evidence by making role-pair gates visibly
   non-neutral.

However, this is still only one seed. It cannot yet justify changing the final
paper claim or launching a full formal 1M/2M batch.

## Next Step

Run the same role-gate prior dev100 protocol for seeds 1 and 2, then repeat the
four-scenario suite selection. If the improvement is stable across seeds, promote
role-gate prior into the main EA-RG-MAPPO-S candidate for longer 1M/2M training.
