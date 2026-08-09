# v1.9 D2 Budget Calibration Protocol

**Status: prepared, not launched.** This is a GPU engineering calibration after
the completed D1 artifact gate. It is not a formal architecture comparison,
checkpoint-selection study, held-out evaluation, ablation, OOD experiment, or
paper evidence.

## Purpose

D2 determines whether the already implemented PCRF training path is practical
at the fixed D1 environment load, and records the cost needed to freeze a
future formal budget. It does **not** decide whether PCRF is better than a
single graph: no comparator is trained in D2.

## Fixed D2 matrix

| Method | encoder | hidden width | engineering seeds | updates |
|---|---|---:|---|---:|
| PCRF | `pcrf` | 128 | 9201, 9202, 9203 | 100 |

The seeds are fresh engineering seeds and may not be reused as formal training,
validation, or confirmatory seeds.

## Fixed common configuration

- 8 environments, 128 rollout steps, PPO epochs 4, CUDA;
- strict recipient-specific sensing/bottleneck;
- communication dropout 0.3, message delay 2, radar dropout 0.1;
- relay 1 failure onset 40, failure duration 80, stable window `K=4`, and
  minimum success step 80;
- validation at updates 1, 20, 40, 60, 80, 100, with eight fixed episodes per
  seed; immutable snapshots and episode event/censor records are mandatory;
- the D1 architecture, actor information contract, packet schema, reward,
  optimizer, learning rate, rollout size, environment count, and hidden width
  are unchanged.

## Required records

Every run must retain training logs, validation summaries, episode records,
snapshot metadata/manifests, and SHA256 values. The launcher additionally
records `/usr/bin/time -v` output per run and 10-second GPU utilization/memory
telemetry for the whole D2 window. The runtime manifest must record CUDA and
the immutable source-archive commit/SHA256 provenance.

## D2 artifact gate

`D2_ARTIFACT_GATE_PASS` requires all three runs to reach update 100, exact
validation updates `[1, 20, 40, 60, 80, 100]`, verified immutable artifacts at
every point, finite logs, CUDA attestation, per-run runtime records, and
nonempty GPU telemetry. It does not report a selected checkpoint and never
interprets RMST or establishment values as method evidence.

## Permitted inference after D2

Only the following may be reported to the author: throughput, validation time,
peak/typical GPU memory, disk growth, whether the training trajectory is
computationally stable, and a cost range for candidate formal budgets. A final
formal budget, seed count, validation population, and confirmatory protocol
require a separate author freeze before any F1 launch.

## Stopping rules

Stop and report without architecture changes if CUDA is unavailable, a run
crashes, NaN/non-finite values appear, any snapshot/event record/hash fails,
or telemetry/runtime provenance is missing. Do not extend past 100 updates,
add comparators, inspect a held-out population, or alter the method after
observing D2 trajectories.
