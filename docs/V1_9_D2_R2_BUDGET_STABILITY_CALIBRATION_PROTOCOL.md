# v1.9 D2-R2 Budget and Stability Calibration Protocol

**Status: `D2_R2_ARTIFACT_AND_STABILITY_GATE_PASS__F1_FORMAL_TRAINING_AUTHORIZED__F2_NOT_AUTHORIZED`.**

## Scope

D2-R2 is a method-blind development calibration. It establishes whether the
three frozen R2 representations train stably through the candidate formal
budget and whether required validation endpoint/artifacts are produced. It is
not confirmatory evidence, a method ranking, or authority to alter PCRF-R2.

Only a common failure across methods can block the candidate budget and require
an author decision. A method appearing worse or better than another is never a
reason to tune the gate, architecture, reward, or training allocation.

## Frozen D2 matrix and common interface

| Method | Encoder | Hidden width | Development seeds | Updates/run |
|---|---|---:|---|---:|
| PCRF-R2 | `pcrf_r2` | 128 | 9501, 9502 | 300 |
| source-aware wider single graph | `single_r2` | 147 | 9501, 9502 | 300 |
| matched-information non-graph | `matched_nongraph_r2` | 152 | 9501, 9502 | 300 |

These six seeds are permanently non-evidentiary and excluded from F1/F2.
Every run uses 8 environments, 128 rollout steps, PPO epochs 4, strict
sensing/bottleneck, dropout 0.30, delay 2, radar dropout 0.10, relay 1 failure
at step 40 for 80 steps, `K=4`, and minimum success step 80. Validation,
snapshot, and event-record points are `1,20,40,...,300`, with 16 fixed
development episodes per run. D2 requires CUDA with at least 16 GiB total GPU
memory; it is not silently replaced by a CPU or sub-specification GPU run.

## Required observations and stopping rules

At every validation point retain immutable actor-critic snapshot, metadata,
SHA256, source commit, episode-level terminal-outcome records, and RMTE
summary. The artifact gate verifies finite PPO quantities, contiguous updates
1--300, empty stderr, all sixteen validation points, R2 encoder provenance,
and frozen event-record fields.

D2 may inspect only numerical stability, runtime, memory/disk footprint,
artifact persistence, and within-run endpoint trajectory adequacy. It must not
report cross-method numerical differences, select scientific winners, or change
a model. Stop on insufficient GPU memory, NaN/non-finite output, stderr,
missing immutable artifact, source mismatch, or failed actor-boundary/D0/P0-A/
P1 deterministic regression.

## Precommitted F1/F2 constants conditional on a passing D2 gate

- F1 seeds: `0,1,2,3,4,5,6,7`, all three R2 methods, 300 updates;
- F1: 8 environments, 128 rollout steps, PPO epochs 4; validation every 10
  updates with immutable snapshots/event records and frozen RMTE selector;
- F2: 300 paired untouched IDs `510000`--`510299` per selected checkpoint;
- primary RMTE80; secondary RMTE220, RMPE80/RMPE220, and establishment,
  terminal-failure, active-unestablished decompositions;
- practical threshold `Delta RMTE80 <= -4` steps (one frozen `K=4` window);
- hierarchical paired bootstrap: training seed outer, matched episode inner,
  10,000 resamples; and
- the common-onset diagnostic remains secondary.

The ordered F2 seed list and common-onset state bank are SHA256 hashed before
their corresponding data are opened. No D2 artifact belongs to F2.

## Exit states

`D2_R2_ARTIFACT_AND_STABILITY_GATE_PASS` permits the F1/F2 freeze manifest at
the constants above and yields `D2_R2_PROTOCOL_FROZEN__READY_FOR_F1_AUTHORIZATION`.
It does not authorize F1. Any common stability/artifact failure yields
`D2_R2_CALIBRATION_BLOCKED`; no architecture change is automatic.
