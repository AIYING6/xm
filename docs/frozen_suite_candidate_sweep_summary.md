# Frozen Four-Scenario Suite Candidate Sweep

Generated: 2026-07-29

## Purpose

This is a low-cost diagnostic under the newly frozen validation protocol. It is
not final paper evidence.

The goal was to check whether the existing dev-1M checkpoints remain promising
when checkpoint selection is performed over a four-scenario relay-failure suite
instead of selecting one checkpoint per scenario.

## Protocol

- scenarios:
  - `dropout030_delay2_relay_failure_early`
  - `dropout030_delay2_relay_failure`
  - `dropout030_delay2_relay_failure_delayed`
  - `dropout030_delay2_relay_failure_late`
- strict target sensing: enabled
- agent target-info bottleneck: enabled
- max target message age: `80`
- checkpoint selection group: `suite`
- validation episodes: `5` per scenario/checkpoint
- base seed: `290000`
- training seeds: `0, 1, 2`
- candidate checkpoints:
  - EA-RG-MAPPO-S: `2200, 3800, 3907`
  - Single-Graph MAPPO: `2200, 3800, 3907`
  - MAPPO/no-graph: `2400, 3800, 3907`
  - HAPPO: `2200, 3800, 3907`

## Selected-Checkpoint Means

| Method | Suite recovery | After-loss recovery | Delayed recovery | Success | Notes |
| --- | ---: | ---: | ---: | ---: | --- |
| EA-RG-MAPPO-S | 0.083 | 0.083 | 0.083 | 0.083 | Only seed 1 is active; seed 0/2 fail. |
| Single-Graph MAPPO | 0.217 | 0.217 | 0.000 | 0.300 | Best broad success/recovery, mainly seed 2. |
| MAPPO/no-graph | 0.133 | 0.133 | 0.000 | 0.217 | Competitive broad baseline, mainly seed 1. |
| HAPPO | 0.000 | 0.000 | 0.000 | 0.000 | Current HAPPO dev-1M checkpoints do not solve this suite. |

## Seed-Level Selected Checkpoints

| Method | Seed | Update | Recovery | Delayed recovery | Success |
| --- | ---: | ---: | ---: | ---: | ---: |
| EA-RG-MAPPO-S | 0 | 3907 | 0.000 | 0.000 | 0.000 |
| EA-RG-MAPPO-S | 1 | 3800 | 0.250 | 0.250 | 0.250 |
| EA-RG-MAPPO-S | 2 | 3907 | 0.000 | 0.000 | 0.000 |
| Single-Graph MAPPO | 0 | 3907 | 0.100 | 0.000 | 0.200 |
| Single-Graph MAPPO | 1 | 3907 | 0.000 | 0.000 | 0.000 |
| Single-Graph MAPPO | 2 | 2200 | 0.550 | 0.000 | 0.700 |
| MAPPO/no-graph | 0 | 3800 | 0.050 | 0.000 | 0.100 |
| MAPPO/no-graph | 1 | 2400 | 0.350 | 0.000 | 0.550 |
| MAPPO/no-graph | 2 | 3907 | 0.000 | 0.000 | 0.000 |
| HAPPO | 0 | 3907 | 0.000 | 0.000 | 0.000 |
| HAPPO | 1 | 3907 | 0.000 | 0.000 | 0.000 |
| HAPPO | 2 | 3907 | 0.000 | 0.000 | 0.000 |

## Interpretation

This diagnostic does not support moving directly to final test evaluation.

Important signals:

- Single-Graph currently has the best broad suite success/recovery in the
  sampled checkpoints.
- MAPPO/no-graph remains competitive, so the task is not yet forcing enough
  useful role-graph dependence.
- EA-RG-MAPPO-S is the only method with non-zero strict delayed recovery in this
  diagnostic, but the signal is seed-fragile and too sparse.
- HAPPO is a valid strong-baseline attempt, but current checkpoints do not solve
  the frozen suite.

The result is scientifically useful because it separates two effects:

- broad success can still come from favorable geometry or simpler graph mixing;
- delayed recovery is closer to the intended kill-chain resilience claim but is
  currently too sparse for final evidence.

## Tooling Fixes

During this diagnostic, HAPPO evaluation was aligned with the 3D checkpoint
sweep:

- `scripts/evaluate_happo_3d.py` now loads older HAPPO checkpoints with the same
  matching-tensor loader used by RI-GMAPPO.
- `scripts/evaluate_happo_checkpoint_sweep.py` now supports
  `--checkpoint-updates`, `--selection-group`, `--selection-metric`,
  `--delayed-recovery-min-step`, and `--selection-success-weight`.
- HAPPO summary rows now populate after-loss and delayed-recovery columns.

Validation passed:

```text
python -m py_compile scripts/evaluate_3d_checkpoint_sweep.py scripts/evaluate_happo_checkpoint_sweep.py scripts/evaluate_happo_3d.py
python scripts/audit_checkpoint_selection_schema.py
python scripts/audit_paper_manifest.py --manifest results/paper_command_manifest.csv
```

## Next Action

Do not run held-out test yet.

Next work should focus on one of two paths:

1. Diagnose why EA seed 0 and seed 2 fail under the suite while seed 1 has the
   only delayed-recovery signal.
2. Run a second candidate sweep with `--selection-metric delayed_recovery` to
   decide whether the formal primary metric should prioritize strict delayed
   recovery rather than broad post-failure recovery.

Only after this should the project scale to 2M/5M training or formal
50/100-episode validation.

## Post-Hoc Delayed-Recovery Selection

A post-hoc suite selection was also computed from the same summary CSV files
without rerunning episodes. The score used:

```text
1000 * delayed_recovery - delayed_recovery_steps
```

with no success bonus. This asks which method has evidence for delayed
post-failure recovery rather than broad fast interception.

| Method | Delayed recovery | Broad recovery | Success | Interpretation |
| --- | ---: | ---: | ---: | --- |
| EA-RG-MAPPO-S | 0.083 | 0.083 | 0.083 | Highest delayed signal, but seed-fragile. |
| Single-Graph MAPPO | 0.017 | 0.050 | 0.083 | Mostly loses advantage when early recoveries are filtered. |
| MAPPO/no-graph | 0.000 | 0.033 | 0.033 | No strict delayed-recovery signal in sampled checkpoints. |
| HAPPO | 0.000 | 0.000 | 0.000 | No strict delayed-recovery signal in sampled checkpoints. |

This supports keeping delayed recovery as a mechanism-hardening metric, but the
absolute values are still too low for final paper evidence. The next experiment
should improve EA training stability and then rerun this suite with a larger
episode count.

## Expanded Candidate Sweep Around Online Peaks

The initial candidate list missed several online-monitoring peaks. A second
resume sweep added:

- EA-RG-MAPPO-S: `1700`, `3200`
- Single-Graph MAPPO: `1200`, `1800`
- MAPPO/no-graph: `500`, `2300`

HAPPO remained at the aligned sweep output because its current candidates were
all zero.

Safety-gated post-hoc suite selection (`collision_mean = 0`) gives:

| Selection metric | Method | Recovery | Delayed recovery | Success |
| --- | --- | ---: | ---: | ---: |
| Broad recovery | EA-RG-MAPPO-S | 0.333 | 0.083 | 0.433 |
| Broad recovery | Single-Graph MAPPO | 0.350 | 0.083 | 0.500 |
| Broad recovery | MAPPO/no-graph | 0.133 | 0.000 | 0.167 |
| Broad recovery | HAPPO | 0.000 | 0.000 | 0.000 |
| Delayed recovery | EA-RG-MAPPO-S | 0.217 | 0.217 | 0.217 |
| Delayed recovery | Single-Graph MAPPO | 0.133 | 0.100 | 0.167 |
| Delayed recovery | MAPPO/no-graph | 0.033 | 0.000 | 0.033 |
| Delayed recovery | HAPPO | 0.000 | 0.000 | 0.000 |

Updated interpretation:

- If the paper emphasizes broad post-failure success, Single-Graph remains a
  very strong competitor and EA does not clearly win.
- If the paper emphasizes strict delayed kill-chain recovery, EA has the
  strongest signal among the current methods.
- The current evidence is still not final because the episode count is only
  `5` per scenario/checkpoint and EA still has a failed seed.

The next training change should target stability rather than new architectural
features: reduce late-policy degradation, select checkpoints by suite
validation, and test whether delayed-recovery-oriented reward/selection improves
EA seed consistency.
