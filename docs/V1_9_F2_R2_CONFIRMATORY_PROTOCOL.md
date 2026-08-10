# v1.9 F2-R2 Untouched Confirmatory Evaluation Protocol

**Authorization:** `F1_R2_FORMAL_TRAINING_COMPLETE__F2_CONFIRMATORY_AUTHORIZED__NO_MORE_TRAINING`.

**Implementation state:** `F2_R2_IMPLEMENTATION_FROZEN__READY_TO_EXECUTE` after
the zero-result synthetic/static gate. This is not an F2 result: no
confirmatory episode has been instantiated by the implementation gate.

## Scope

F2 evaluates only the 24 checkpoint hashes frozen in
`F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json`.  It may not train, resume training,
select another checkpoint, alter a hyperparameter, replace an episode, add an
episode after inspection, or open any OOD/mechanism/ablation population.

Before any confirmatory environment is instantiated, the evaluator must write
an immutable `F2_R2_LAUNCH_PREFLIGHT_MANIFEST.json` that verifies the F1
selection and artifact-gate hashes.  This is a zero-result check: it reads
checkpoint bytes but does not create an F2 episode or report performance.

## Frozen matrix and pairing

| Item | Frozen value |
|---|---|
| Methods | `pcrf_r2`, `single_r2`, `matched_nongraph_r2` |
| Training seeds | `0`--`7` for every method |
| Checkpoint | The selected F1 checkpoint SHA256 for each method/seed |
| Confirmatory IDs | `510000`--`510299` |
| Episodes | 300 **per selected checkpoint** |
| Pairing | The same ordered ID is used for every method and every matched training seed |
| Total rollouts | 24 × 300 = 7,200 |
| Policy action | Deterministic argmax action |

The evaluation environment uses the frozen formal conditions: 3DOF intercept,
strict target sensing and actor bottleneck, communication dropout `0.30`,
message delay `2`, radar dropout `0.10`, relay agent `1` failure from step `40`
for `80` steps, stable window `K=4`, and minimum success step `80`.

## Endpoints and analysis

The primary contrast is PCRF-R2 versus source-aware `single_r2`:

\[
\Delta RMTE80 = RMTE80^{PCRF-R2} - RMTE80^{single-R2}.
\]

Negative values favor PCRF-R2.  The pre-frozen practical threshold is
\(\Delta RMTE80 \le -4\) steps.  `RMTE220`, establishment, terminal-failure,
active-not-established, `RMPE80`, and `RMPE220` are reported as pre-frozen
secondary endpoints. `matched_nongraph_r2` is a secondary structural
comparator.

The analysis uses 10,000 hierarchical paired bootstrap resamples: matched
training seed first, then matched episode within seed. Episode pooling must not
replace training-seed replication. Terminal failures contribute the restriction
horizon to RMTE; they are not ordinary right-censoring.

## Output isolation and stopping

The launcher log may report only progress and integrity failures until all
7,200 rollouts finish. It must not print a method-level metric while the run is
partial. Raw episode records, per-checkpoint summaries, hashes, and the final
analysis are immutable and written to a new F2-only output directory.

Any missing checkpoint, hash mismatch, source mismatch, duplicate/missing
episode, nonempty evaluator error log, or interrupted execution stops the
pipeline without replacing completed episodes. A recoverable engineering
restart must use the same frozen F2 plan and preserve prior immutable records.

F2 completion does not itself authorize mechanism diagnostics, ablations, OOD,
or a manuscript superiority claim. The author reviews the complete F2 artifact
set before choosing the next stage.
