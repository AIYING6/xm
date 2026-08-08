# FORMAL_V1_8_TRAINING_REPORT

**Scope completed:** the authorized 3-method × 3-seed formal training and frozen
validation only. Confirmatory held-out evaluation, OOD, relation-conflict
performance evaluation, ablations, and manuscript edits were not run.

## Run completion and integrity

All 9 runs completed 300/300 updates:

| method | seeds | output roots |
|---|---|---|
| corrected EA-RG Full (`multi_relation`) | 0, 1, 2 | `results/formal_v1_8/ea_rg_seed*` |
| corrected wider single-graph (`single`) | 0, 1, 2 | `results/formal_v1_8/single_seed*` |
| matched-information non-graph (`matched_nongraph`) | 0, 1, 2 | `results/formal_v1_8/matched_nongraph_seed*` |

No run emitted a crash, traceback, boundary-test failure, or non-finite loss or
training reward. `eval_intent_acc=nan` is expected because the optional intent
auxiliary head is disabled; it is not a training NaN. The persistent failure
configuration was explicit in every command: relay agent 1, onset 40, duration
80, with `K=4` independent and tau 80/220 frozen.

## Learning diagnostics

Training-return AUC is the trapezoidal mean of `train_avg_reward` over the 300
updates. Establishment-rate AUC is computed over the 31 logged validation
points. Values are engineering diagnostics, not confirmatory evidence.

| method | reward AUC mean ± seed SD | establishment AUC mean ± seed SD | final reward mean ± seed SD |
|---|---:|---:|---:|
| EA-RG | 0.02196 ± 0.00787 | 0.00446 ± 0.00773 | 0.04255 ± 0.02425 |
| wider single | 0.02117 ± 0.00818 | 0.02731 ± 0.03925 | 0.07930 ± 0.01522 |
| matched non-graph | 0.00488 ± 0.00360 | 0.01421 ± 0.01804 | 0.05219 ± 0.02449 |

The AUCs are not used to reorder methods or alter the frozen architecture.

## Frozen validation selection

Validation used 20 episodes per trained-seed checkpoint with seeds
`10000 + 100*training_seed + episode_index`, formal stochastic parameters, and
the censoring-aware ordering RMST80 → establishment probability/censoring →
RMST220 → earlier update.

| method | seed | selected update | RMST80 | establishment | censoring | RMST220 |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG | 0 | 300 | 80.0 | 0.10 | 0.90 | 208.35 |
| EA-RG | 1 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |
| EA-RG | 2 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |
| wider single | 0 | 300 | 80.0 | 0.45 | 0.55 | 186.5 |
| wider single | 1 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |
| wider single | 2 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |
| matched non-graph | 0 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |
| matched non-graph | 1 | 300 | 79.7 | 0.25 | 0.75 | 197.35 |
| matched non-graph | 2 | 300 | 80.0 | 0.00 | 1.00 | 220.0 |

### Selection-protocol deviation

The launch commands omitted `--save-snapshots`. Consequently, only the final
update-300 checkpoint was available to the selector; the reported selection is
a valid frozen-validation evaluation of that checkpoint but not a comparison
among intermediate checkpoints. This is recorded as a protocol deviation and
must not be silently described as full trajectory checkpoint selection. No
confirmatory evaluation should use a different checkpoint-selection story.

## Timing and stop rule

Filesystem completion timestamps indicate approximately 1 h 42 min for the
matched non-graph group, 2 h 19 min for the single-graph group, and 3 h 18 min
for the EA-RG group under the parallel CPU launch. These are measured wall-clock
approximations, not GPU benchmarks.

Training and validation are complete. Stop here and await author direction on
the recorded snapshot/selection deviation before any confirmatory held-out
evaluation.
