# v1.9 D2 Budget Calibration Protocol

**Status: SUPERSEDED_AND_BLOCKED_BY_G0. Do not launch this protocol.** The initial D2
launcher stopped at its first training command
because the AutoDL image lacked `/usr/bin/time`; no seed or update was trained.
Its incomplete output is retained as an engineering audit trail. D2-R1 replaces
that unavailable external utility with a repository-contained portable timing
recorder and uses a separate output root and protocol identifier. The
subsequent PCRF-R1 theory freeze changed fusion semantics, so this launcher
must not be started until PCRF-R1 has passed a fresh D1-R1 CUDA/artifact gate.
It is not a formal architecture comparison, checkpoint-selection study,
held-out evaluation, ablation, OOD experiment, or paper evidence.

## Historical purpose and supersession

This document records the pre-G0 D2-R1 engineering design.  It cannot measure
the final PCRF-R1 budget because it predates the G0 finding that the current
Task-Support relation is exactly duplicated from Communication.  It is retained
for its timing/artifact specification, not as an authorized launcher.

After an author resolves the G0 No-Go and freezes the final theory, the
replacement D2 must train **all three** primary representations (PCRF, wider
single graph, and matched-information non-graph) with one or two fresh
engineering seeds each under a common environment and update budget.  Its
permitted inference remains strictly engineering/method-blind: throughput,
memory, disk, numerical stability, and endpoint information adequacy.  It
cannot choose a winner, select a checkpoint for confirmation, or alter the
scientific contract.

## Superseded fixed D2 matrix (not for execution)

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
- PCRF-R1 baseline-plus-conflict fusion is fixed by
  `V1_9_PCRF_R1_THEORY_FREEZE.md`; actor information contract, packet schema,
  reward, optimizer, learning rate, rollout size, environment count, and hidden
  width are unchanged.

## Required records

Every run must retain training logs, validation summaries, episode records,
snapshot metadata/manifests, and SHA256 values. D2-R1 additionally records an
immutable repository-contained wall/CPU timing JSON per run and 10-second GPU
utilization/memory telemetry for the whole D2-R1 window. The runtime manifest must record CUDA and
the immutable source-archive commit/SHA256 provenance. The operator must pass
these two values explicitly as `SOURCE_COMMIT` and `SOURCE_ARCHIVE_SHA256` at
launch; the launcher deliberately has no fallback value that could describe an
older archive.

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
observing D2 trajectories. PCRF-R1 D1 failure stops D2 rather than permitting
an unreviewed architecture repair.
