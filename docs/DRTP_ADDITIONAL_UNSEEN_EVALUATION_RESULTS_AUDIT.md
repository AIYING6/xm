# DRTP Additional Unseen-Condition Evaluation Results Audit

## Integrity

- Source archive: `drtp_additional_unseen_evaluation_results.tar.gz`
- SHA256: `95695bf4522877d2a79dcb4e46245ae3467641efa06ca6440e4be48afc82a7bf`
- Status: `ADDITIONAL_UNSEEN_EVALUATION_COMPLETE`
- Training started: `false`
- Raw records: `12,000 / 12,000`
- Checkpoint cells: 20 final checkpoints: UTR and DRTP for both the formal
  2301--2305 cohort and the independent 2401--2405 cohort.
- Tape: `510000--510099`, SHA256
  `efa090210ded72c0eb48120f71298a747f1c5ac9f64c60bc4a080677b03f0d4c`.
- All scheduled episodes were retained, risk-set trigger validity was 1.000 in
  every method--seed--condition cell, and cross-cohort pooling was prohibited.

## Frozen unseen members

The evaluation used `(20,80)`, `(68,80)`, `(44,20)`, `(44,140)`, `(20,140)`,
and `(68,40)` as `(onset,duration)` pairs.  None belongs to the eleven specific
onset--duration members in the DRTP training support.

## Stratified paired result

The formal cohort's mean DRTP--UTR task-score differences across the six members
range from `+35.36` to `+70.85`; every median is positive and each condition has
`4/5` or `5/5` positive paired seeds.  The independent cohort's corresponding
means range from `-25.20` to `-49.46`; every median is negative and each
condition has only `1/5` or `2/5` positive seeds.

This strengthens two bounded statements simultaneously:

1. Within the already favorable formal cohort, the observed task-score advantage
   extends to these six training-unseen condition members.
2. The sign reversal between the formal and independent training cohorts also
   persists on the same newly frozen members.

It does **not** create a preregistered confirmatory OOD result, justify pooling
the cohorts, establish generalization beyond this environment, establish a causal
training-failure mechanism, or support a training-seed-stability claim.

## Stop rule

The evaluation does not authorize follow-on training, sampler changes, or a new
DRTP variant.  Its sole permitted use is transparent manuscript evidence
integration and the submission-stage reliability boundary.
