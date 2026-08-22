# DRTP-STAB-A0 Historical Replay

## Replay eligibility

Offline replay of EMA difficulty, inertial weights, or a weight trust region
requires the historical pre-weight difficulty sequence (or the aligned
completed-return/EMA sequence) for each seed. The frozen code alone is
insufficient because those signals are policy-trajectory dependent.

Those sequences are absent from the currently available historical assets.
Consequently no R1/R2/R3 replay was executed, no smoothing coefficient was
selected, and no future method hyperparameter was inferred.

## Why a synthetic replay is prohibited

Replaying the rule with invented difficulty values, terminal q values, or
one-update technical-smoke data would not answer the A0 question and would
create a false impression of evidence. It could neither establish reduction of
bad-seed instability nor preservation of good-seed adaptive focus.

## UTR distance

`D_to_UTR` cannot be quantified without full trajectories. The terminal
seed2002 weights are visibly non-uniform, but a snapshot cannot show whether a
candidate smoothing transform would remain meaningfully adaptive over time.

`artifacts/drtp_stab_a0/replay_summary.csv` records this non-execution
explicitly.
