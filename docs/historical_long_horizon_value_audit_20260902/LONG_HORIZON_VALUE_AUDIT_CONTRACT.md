# Long-horizon value audit contract

Protocol: `HISTORICAL-CANDIDATE-LONG-HORIZON-VALUE-AUDIT-V1`

## Authorized work

This is a read-only artifact audit. It inspects historical training lengths, checkpoint availability, completed matched performance outcomes, and training-curve maturity evidence. It does **not** assert that a training objective curve is a task-performance curve.

## Prohibitions

new training, rollout, evaluation, parameter adjustment, seed change, checkpoint promotion, new algorithm, A-line modification, automatic continuation.

## Decision standard

`LONG_HORIZON_RETEST_JUSTIFIED` requires: a local matched performance signal, clearly sub-mature historical budget, no evidence of mature negative replication, observable evidence that the relative ranking might change with horizon, exact frozen semantic recovery, and no parameter adjustment. `WEAKLY_JUSTIFIED` means local upside survives but the direct long-horizon rationale is missing. `NOT_JUSTIFIED` means a longer comparable failure exists or the record supplies no evidence that time, rather than cohort dependence, caused the result.
