# UTR One-Shot Telemetry Numerical-Tolerance Amendment V2

## Immutable prior evidence

This amendment preserves both prior attempt directories and their gate
records.  The first used an absolute-only aggregate comparison.  The second
used `abs_tol=1e-5, rel_tol=3e-8`, passed its 35-cell preflight, then stopped
during the frozen acquisition at UTR seed 2101, `timing_28_80`, episode
440012.  No partial telemetry episode is used for mechanism inference.

The stop record was:

```text
traveled_distance: 121645.02322387695 vs 121645.02713012695
absolute error: 0.00390625
relative error: 3.21118757762e-08
```

The strict historical-evaluator versus passive-logger comparison remained
identical.  The disagreement is only between the logger's Python float64
reduction and the archived legacy Phase-D CSV reduction.

## V2 frozen rule

The only revised comparator is **logger summary versus archived Phase-D
aggregate CSV** for non-integer numeric fields:

```text
abs_tol = 1e-5
rel_tol = 1e-7
```

At `1.6e5` accumulated travel distance, this permits `0.016`, approximately
one to two IEEE-754 float32 accumulation units.  This is a representation
compatibility envelope, not a policy-performance tolerance.

The following remain exact or independently strict:

- historical evaluator versus passive logger: `abs_tol=1e-6`, `rel_tol=0`;
- terminal step, path-switch count, terminal reason, collision, timeout,
  constraint, failure exposure, support/path and all categorical semantics;
- checkpoint hashes, tape IDs, conditions, seeds, policy/environment/reward
  behavior, and telemetry schema.

## One final execution rule

The next attempt uses a new, empty output directory and the identical frozen
five checkpoints, seven conditions, and first 50 existing tape IDs.  If a
semantic mismatch occurs, or a numeric archived-aggregate discrepancy exceeds
this V2 float32 envelope, acquisition stops as `TECHNICAL_INVALID`; no third
tolerance increase is permitted.

No training, optimizer update, continuation, new evaluation tape, seed
change, checkpoint promotion, algorithm change, or environment modification
is authorized.
