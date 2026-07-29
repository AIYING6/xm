# HAPPO Strong-Protocol Comparison Summary

Last updated: 2026-07-29

## Protocol

HAPPO was rerun under the same strong post-loss recovery development protocol
used for the EA/Single/MAPPO comparison.

- Seeds: 0, 1, 2.
- BC: 120 balanced offset geometric demonstration episodes, 20 epochs,
  attacker action weight 2.0.
- PPO: 40 updates, 8 envs, 128 rollout steps.
- PPO settings: learning rate `5e-5`, clip `0.1`, PPO epochs `2`, entropy
  coefficient `0.003`.
- Scenario knobs: strict target sensing, target-info bottleneck, dropout `0.30`,
  message delay `2`, relay failure agent `1`, random failure start `[25, 70]`,
  failure duration `80`.
- Recovery shaping: `min_success_step=80`, post-loss chain reclosure bonus `0.5`
  after step 80.
- Safety: proximity distance `2500`, penalty weight `0.5`.
- Checkpoint candidates: updates 20, 30, 40.
- Validation scenarios:
  - `dropout030_delay2_relay_failure_early`
  - `dropout030_delay2_relay_failure`
  - `dropout030_delay2_relay_failure_delayed`
  - `dropout030_delay2_relay_failure_late`
- Selection: suite-level delayed recovery, `delayed_recovery_min_step=80`,
  success weight `0`.

Outputs:

- Training root:
  `results/paper_config_runs/stability_dev/happo_strong_offset_balanced_recovery_bc_safety05/`
- Sweep root:
  `results/paper_config_runs/stability_dev/checkpoint_sweeps/happo_strong_offset_balanced_recovery_bc_safety05_seed0_2_dev40/`

## BC Quality

The HAPPO BC stage completed for all seeds.

| Seed | Demo success | Final action acc. | Final attacker acc. |
|---:|---:|---:|---:|
| 0 | 0.908 | 0.483 | 0.450 |
| 1 | 0.908 | 0.480 | 0.426 |
| 2 | 0.917 | 0.478 | 0.439 |

This is comparable to the earlier no-graph style BC accuracy range, so HAPPO is
not being evaluated from an intentionally weak random initialization.

## Selected Checkpoints

| Seed | Selected update | Success | Post-loss recovery | Delayed recovery | Collision |
|---:|---:|---:|---:|---:|---:|
| 0 | 20 | 0.425 | 0.475 | 0.200 | 0.000 |
| 1 | 40 | 0.075 | 0.200 | 0.050 | 0.000 |
| 2 | 40 | 0.000 | 0.100 | 0.000 | 0.050 |
| Mean | - | 0.167 | 0.258 | 0.083 | 0.017 |

## Interpretation

HAPPO remains substantially weaker than the graph-based methods under this
strong post-loss recovery protocol, even after behavior cloning. Its selected
mean success and delayed recovery are also below the MAPPO/no-graph baseline
from the same development family.

This supports using HAPPO as a standard external MARL baseline, but it should not
be overemphasized in the paper. The useful conclusion is narrow:

> A standard heterogeneous-agent PPO baseline without graph-structured
> communication is not sufficient for this strict-sensing relay-failure recovery
> task.

The main method claim should still focus on:

1. Graph-based coordination versus no-graph baselines.
2. EA multi-relation graph versus Single-Graph MAPPO as a mechanism and
   interpretability/safety comparison, not as a broad dominance claim.

## Next Step

The fair baseline set for this development protocol now includes:

- EA-RG-MAPPO.
- Single-Graph MAPPO.
- MAPPO/no-graph.
- HAPPO.

Next, create a single merged comparison table for these four methods and then
decide whether to:

- launch a longer 1M/2M formal training batch with the current method, or
- first run the role-gate prior 100-update diagnostic to strengthen the
  multi-relation mechanism.
