# DRTP Additional Unseen-Condition Evaluation Contract V1

## Purpose and scope

This is a one-time, zero-training, post hoc **additional held-out evaluation** of
already frozen final checkpoints.  It is not part of the original prospective
confirmation contract and must not be described as preregistered confirmation.
Its sole purpose is to test whether the already observed DRTP--UTR contrast is
also visible at failure timings and durations absent from the training support.

No training, checkpoint selection, model modification, sampler modification,
PPO modification, or seed replacement is authorized by this contract.

## Frozen checkpoint set

All completed final checkpoints in both paired UTR--DRTP cohorts are included:

| Cohort | Training seeds | Methods | Checkpoint |
| --- | --- | --- | --- |
| Formal prospective cohort | 2301--2305 | UTR-SG-MAPPO, DRTP-SG-MAPPO | final 10M checkpoint |
| Independent replication cohort | 2401--2405 | UTR-SG-MAPPO, DRTP-SG-MAPPO | final 10M checkpoint |

Thus the evaluation contains 20 checkpoint cells.  No MAPPO-NoGraph or SNR
checkpoint is included: they answer external-reference and mechanism-control
questions, respectively, rather than the paired DRTP reliability question.

## Training-support exclusion audit

The DRTP training support contains the nominal condition, F0 `(44, 80)`, timing
members `(28, 80)`, `(36, 80)`, `(52, 80)`, `(60, 80)`, duration members
`(44, 40)`, `(44, 60)`, `(44, 100)`, `(44, 120)`, and compound members
`(28, 120)`, `(60, 120)`, where each tuple is `(failure onset step, duration
steps)`.  The following six held-out members are pairwise distinct from that
support and are frozen before outcome collection:

| Name | Onset | Duration | Coverage role |
| --- | ---: | ---: | --- |
| `unseen_t20_d80` | 20 | 80 | earlier timing |
| `unseen_t68_d80` | 68 | 80 | later timing |
| `unseen_t44_d20` | 44 | 20 | shorter duration |
| `unseen_t44_d140` | 44 | 140 | longer duration |
| `unseen_c20_d140` | 20 | 140 | early-long compound |
| `unseen_c68_d40` | 68 | 40 | late-short compound |

All failures remove relay node 1's legal communication edges according to the
unchanged environment semantics.  Horizon, reward, actor information boundary,
and all evaluator logic remain unchanged.

## Evaluation tape and execution

- A new deterministic tape uses episode IDs `510000--510099` (100 episodes per
  condition), shared across all checkpoint cells and conditions.
- The tape is development/diagnostic evidence and is disjoint from the 490k and
  500k tapes.  It is saved with a SHA256 manifest before evaluation starts.
- Required raw size: `20 cells × 6 conditions × 100 episodes = 12,000` records.
- Every scheduled episode is retained.  Pre-trigger terminations remain in all
  unconditional performance and safety denominators.
- Large evaluation runs only on the cloud with maximum safe worker parallelism;
  it is not executed on the local workstation.

## Reporting and interpretation

For each cohort, condition, and paired seed, report `J`, collision, timeout,
constraint violation, survival-to-onset fraction, risk-set trigger validity,
and paired `DRTP - UTR` effects.  Summaries report mean, median, win count,
worst paired difference, and seed-level values.

The paper may call this an *additional unseen-condition evaluation* or
*exploratory held-out condition evaluation*.  It may not call it the original
confirmatory OOD test, evidence of universal generalization, or evidence that
DRTP is seed-stable.  Results from the formal and independent cohorts are never
pooled into one homogeneous training-seed estimate; their directional contrast
is itself part of the reliability evidence.

## Stop rule

After the single evaluation and its integrity audit, no result triggers further
training or a DRTP redesign.  The result only updates the manuscript's evidence
boundary and is reported whether favorable, mixed, or unfavorable.
