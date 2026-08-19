# UTR One-Shot Telemetry Numerical-Tolerance Amendment

## Scope

This amendment changes **only** the archived-aggregate comparison used by
the passive UTR one-shot telemetry logger.  It does not alter a checkpoint,
policy, environment transition, reward, failure descriptor, evaluation ID,
or telemetry field.

## Trigger

The first local preflight replay completed all 35 fixed cells.  In every
cell, the historical evaluator replay and the logger replay agreed under the
strict evaluator/logger comparison.  The archived Phase-D CSV nevertheless
showed small numerical differences in float-heavy aggregate fields, for
example:

```text
J: 170.69778941292316 vs 170.69778650719672
traveled_distance: 152334.05892944336 vs 152334.05960083008
```

The differences are respectively about `3e-6` and `6.7e-4`, while the latter
aggregate is about `1.5e5`.  Terminal step, failure exposure, terminal
reason, collision, timeout, constraint, path, and all evaluator/logger
semantic comparisons remained identical.

## Frozen comparison rule

Two comparisons remain distinct:

1. **Evaluator versus logger replay:** absolute tolerance `1e-6`, with no
   relative tolerance.  This protects logger semantic invariance.
2. **Logger replay versus archived Phase-D aggregate CSV:** `abs_tol=1e-5`
   and `rel_tol=3e-8` for non-integer numerical summaries.  Integer and
   categorical fields remain exact.  At the largest observed distance scale
   this permits at most about `0.0048`, below one float32 accumulation unit.

Every historical-aggregate mismatch continues to record absolute and
relative error.  The prior failed preflight artifact is retained under a
separate, timestamped diagnostic directory; the corrected attempt must use a
fresh output directory.

## Prohibited changes

No training, checkpoint selection, continuation, new tape, new condition,
seed substitution, model/environment/reward/PPO modification, or telemetry
schema change is authorized by this amendment.
