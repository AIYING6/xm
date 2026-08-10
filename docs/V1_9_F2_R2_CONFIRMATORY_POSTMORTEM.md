# v1.9 F2-R2 confirmatory result lock and read-only postmortem

**Status:** `F2_CONFIRMATORY_COMPLETE__PRIMARY_ARCHITECTURE_SUPERIORITY_NOT_SUPPORTED`.

This is a result lock for the completed, untouched F2 evaluation. It does not
change the F2 protocol, rerun an episode, replace a checkpoint, promote a
secondary endpoint, or authorize additional training.

## Artifact receipt and integrity

- F1 formal artifact archive was received locally as
  `F1_R2_FORMAL_3041e99.tar.gz` (1,413,373,977 bytes). Its tar stream can be
  enumerated without an error.
- F2 confirmatory archive was received locally as
  `F2_R2_CONFIRMATORY_d923781.tar.gz` (25,862 bytes). Its local SHA256 is
  `f51666e5ae33d084748385d4505d2ed1796ad25356ff76937b12a9ec98efc043`,
  matching the SHA256 printed by the AutoDL source instance.
- The archived F2 output contains the launch preflight, 24 isolated worker
  logs, 24 per-checkpoint episode-record CSV files, 24 summaries, execution
  manifest, artifact-gate manifest, and frozen analysis JSON.
- The execution log reports
  `F2_R2_CONFIRMATORY_ARTIFACT_GATE_PASS: 24 checkpoints x 300 paired episodes`.
  The frozen analysis reports 10,000 paired hierarchical bootstrap resamples.

Consequently, this is not a missing-data, hash, pairing, or incomplete-run
failure. The confirmatory data are valid negative evidence for the pre-frozen
primary claim.

## Pre-frozen primary decision

The primary contrast was PCRF-R2 minus source-aware `single_r2` on RMTE80,
where negative values favor PCRF-R2 and the pre-frozen practical threshold was
`delta <= -4` steps.

| Item | PCRF-R2 | single-R2 | Frozen comparison result |
|---|---:|---:|---|
| RMTE80 | 80.0 | 80.0 | delta = 0.0; 95% bootstrap CI [0.0, 0.0] |
| Establishment by 80 | 0/2,400 | 0/2,400 | no primary-window event in either primary method |
| Seed-level RMTE80 delta | -- | -- | 0.0 for all 8 matched training seeds |
| Terminal failure by 80 | 0.0 | 0.00125 | no PCRF safety trade-off, but no efficacy difference |

**Decision:** the source-preserving architecture-superiority claim is not
supported. The null result also fails the practical-effect threshold; it is
not merely a wide-interval result.

## What the immutable records show

The primary window is saturated for the primary comparison, but the full
220-step records are not empty:

| Method | Establishments by 220 / 2,400 | Earliest establishment time after onset | Median establishment time after onset | Terminal outcomes |
|---|---:|---:|---:|---:|
| PCRF-R2 | 237 (9.875%) | 84 | 147 | 0 |
| single-R2 | 55 (2.292%) | 107 | 140 | 4 collisions |
| matched-nongraph-R2 | 56 (2.333%) | 79 | 114 | 1 collision |

The pre-frozen secondary PCRF-minus-single estimates are directionally
favorable at 220 steps, but cannot replace the primary result:

- RMTE220 delta = -5.511; 95% CI [-13.928, 0.571]; 4/8 seed-level effects are
  favorable.
- Establishment-incidence220 delta = +0.0758; 95% CI [0.0004, 0.1946]; only
  4/8 seed-level effects are favorable.
- RMPE220 delta = -7.482; 95% CI [-16.601, -0.218]; 5/8 seed-level effects are
  favorable. RMPE remains a secondary physical-engagement-readiness measure,
  not capture, interception completion, or mission success.

The grouped seed outcomes are highly heterogeneous: for example, PCRF-R2
establishment counts range from 0 to 134 out of 300. This is why pooling
episodes cannot replace the frozen training-seed hierarchy.

## Interpretation of the RMTE80 saturation

The F2 environment froze relay failure at global step 40 for 80 steps, with a
four-step stability window and RMTE measured from failure onset. The raw record
audit confirms that the earliest observed PCRF-R2 establishment is at onset +84
and the earliest observed single-R2 establishment is at onset +107. Thus the
80-step primary window contained no primary-method establishment event.

The simulator code does not impose a literal rule that establishment is
impossible during relay failure: a chain can close if the physical and
communication predicates are met. Therefore the correct conclusion is not
"the event was hard-coded to be impossible." The correct conclusion is that,
under the frozen policy population and confirmatory scenario, the primary
window was empirically non-discriminative for the primary comparison. The
post-failure task dynamics, sustained relay loss, and stability requirement
together produced a horizon that was too short to test the intended
architecture contrast.

## Scientific consequences

1. Do not claim PCRF-R2 superiority, post-onset conflict-handling superiority,
   or a successful primary architecture comparison.
2. Do not relabel RMTE220/RMPE220 as a primary endpoint, extend the 300-update
   budget, replace seeds, alter selection, or rerun F2. Each would be a
   post-result modification.
3. Do not start mechanism ablations, OOD, or a paper Results section intended
   to establish PCRF-R2 superiority. Those studies cannot rescue a failed
   confirmatory primary claim.
4. Retain the v1.9 result as valid evidence of a task/endpoint adequacy
   failure, together with its information-boundary, provenance, and terminal
   estimand improvements.

## Next permitted work

The next research decision is a new R3 design decision, not a v1.9 repair
run. A prospective R3 protocol must first demonstrate on method-blind
development rollouts that its primary post-failure window has non-saturated
event incidence, while retaining the recipient-specific information contract,
matched source-aware comparator, terminal-outcome semantics, and untouched
confirmatory evaluation. It may not choose a new horizon or failure condition
by selecting the most favorable v1.9 F2 cell.
