# Phase S3-R Evaluation Remediation and Learnability Diagnosis Protocol

**Protocol ID:** `PHASE-S3-R-V1`  
**Status:** FROZEN BEFORE RE-EVALUATION  
**Artifact class:** DEVELOPMENT_ONLY / READ-ONLY CHECKPOINT RE-EVALUATION

## Purpose

S3 completed nine fixed-budget training runs but its original evaluation used
method-specific episode-ID ranges, so method contrasts did not share an
identical evaluation tape. It also inherited `success_min_step: 1000` while
the fixed horizon is 260 steps; consequently, the recorded success diagnostic
was structurally always zero. S3-R repairs these two evaluation defects using
only the nine existing fixed final checkpoints and archived training logs.

S3-R does **not** repair or relaunch the S3 training runs, select checkpoints,
alter the S2 geometry/failure/observation/reward contract, or produce
canonical evidence.

## Frozen input evidence

- archived source package:
  `archival/provenance/phase_s3_cloud_a4f2076/`;
- exact training commit: `a4f2076a38da86d528890f4fbdc8019bff4fb365`;
- methods: MAPPO, Parameter-Matched Single-Graph, Multi-Relation Full;
- development training seeds only: `1501`, `1502`, `1503`;
- one fixed final checkpoint per method x seed, with no checkpoint promotion.

## Re-evaluation contract

For every training seed, all three methods evaluate the same 100 deterministic
nominal/failure episode pairs. The shared S3-R IDs are `340000` through
`340099`; an episode's seed is its ID. Within a pair, every exogenous
realization is identical and only the Relay-1 intervention differs:

- nominal: no failed node;
- failure: Relay 1, onset step 44, duration 80 steps.

All S2 environment semantics remain unchanged: business-grounded geometry,
strict sensing, legal information bottleneck, direct Scout--Attacker edge
allowed, 260-step horizon, target policy `straight`, and no dropout or delay.

## Success-metric amendment

The legacy S2 field `success_min_step: 1000` is retained as archival fact and
the original S3 success results are never overwritten. For S3-R only, the
development diagnostic `success_at_horizon` is computed with
`min_success_step = max_steps = 260`. This is an end-of-horizon task-completion
indicator; it cannot terminate an episode before its frozen 260-step horizon.
It changes neither dynamics, actions, rewards, failure timing, nor `J`.

`success_at_horizon` is secondary. The S3 primary diagnostic remains
`Delta_J = J_nominal - J_failure`, always interpreted together with
`J_nominal` and `J_failure`.

## Mandatory integrity checks

1. Every checkpoint SHA256 matches its archived manifest.
2. All three methods have exactly the same IDs per training seed and condition.
3. Nominal/failure pairs match within each method and training seed.
4. Each failure episode is exposed at the frozen onset/duration.
5. The evaluator is deterministic on a replayed method/seed/condition/ID.
6. Existing S3 evidence remains unmodified; S3-R outputs go only under
   `results/development/phase_s3r_evaluation_remediation/`.

## Learnability diagnosis

Archived `train_log.csv` files are read without mutation. For every
method x seed, S3-R reports early/middle/final-window mean training reward,
final-window slope, and final finite PPO diagnostics. These descriptive traces
may distinguish an obviously still-rising curve from an apparent plateau, but
they do not authorize selective extra training.

## Decision rule

S3-R can only return one of the following:

- **TRAINING-BUDGET-DIAGNOSIS-REQUIRED:** Full has non-degenerate nominal
  competence and its shared-tape evidence is compatible with later but
  unfinished learning. A new, equal-budget, three-method development protocol
  would then be required before any new training.
- **ARCHITECTURE-DIAGNOSIS-REQUIRED:** Full remains nominally non-competitive
  or no coherent shared-tape robustness signal appears. Any architecture change
  requires a new separately frozen protocol.
- **INCONCLUSIVE:** an integrity/determinism gate fails.

S3-R never authorizes S4, canonical seeds, or Phase 3A.
