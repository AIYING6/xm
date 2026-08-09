# D1-R2 Engineering-Only Protocol

## Status and scope

`D1_R2_ENGINEERING_AUTHORIZED__PERFORMANCE_USE_PROHIBITED`

This protocol is an implementation and artifact gate for the frozen
source-separated PCRF-R2 line.  It is not a method experiment, a budget
calibration, a selection of a scientific winner, or confirmatory evidence.
No D1 value, curve, checkpoint, or rank may be used in the manuscript or in a
method-design decision.

## Frozen short-run matrix

Six serial engineering runs are required:

| Method label | Actor encoder | Engineering seeds | Updates per completed run | Hidden dimension |
| --- | --- | --- | ---: | ---: |
| `pcrf_r2` | `pcrf_r2` | 9201, 9202 | 30 | 128 |
| `single_r2` | `single_r2` | 9201, 9202 | 30 | 147 |
| `matched_nongraph_r2` | `matched_nongraph_r2` | 9201, 9202 | 30 | 152 |

The seeds are engineering-only and are permanently excluded from every future
F1/formal seed set.  Capacity is frozen before execution: 169,977 PCRF-R2
parameters, 170,784 single-R2 parameters (0.47% gap), and 169,141
matched-nongraph-R2 parameters (0.49% gap).

Every run uses 8 environments, 128 rollout steps, 4 PPO epochs, the existing
frozen communication/failure settings, CUDA, and validation at updates 1, 10,
20, and 30.  To exercise genuine continuation, each run is executed as an
initial 10-update segment followed by a 20-update resume segment.  This is one
30-update engineering run, not a performance extension.

## Required immutable artifacts

At each validation update the run must retain an immutable
`actor_critic_update_XXXX.pt`, metadata, episode-level event record, validation
summary, and hash/provenance manifest.  The source tree must be a clean Git
checkout at the launcher-provided expected commit; archive-only deployment is
not sufficient for this gate.  The resume segment must use that same commit,
run ID, method/seed configuration, and protocol identifier.

The frozen selector is executed only to verify that all required selector
fields and snapshots can be read: lower RMST80; higher establishment
probability; lower censoring; lower RMST220; earlier update.  Its output is an
artifact diagnostic and is not a selected scientific checkpoint.

## Permitted questions

Only these questions may be answered: startup; forward/backward/PPO stability;
CUDA, memory and batch compatibility; immutable snapshot persistence;
episode-event record completeness; frozen metric computation; SHA256 and
provenance integrity; resume continuity; and use of the source-separated R2
actor interface in the real rollout path.

## Prohibitions

Do not compare methods, interpret RMST or learning curves, tune any method,
alter architecture/reward/failure/K/tau/gate/selector, open confirmatory
held-out data, run D2/formal training/ablations/OOD, or revise the paper from
D1 output.

## Gate

`D1_R2_ARTIFACT_GATE_PASS` is possible only when all six runs reach update 30,
all required artifacts verify, both continuation segments complete without
NaN/exception, the source commit/protocol/method/seed provenance agrees, and
the actor-boundary and D0-R2 tests still pass.  Any failure stops the line for
an implementation repair and D0-to-D1 repeat; it cannot motivate a PCRF design
change.
