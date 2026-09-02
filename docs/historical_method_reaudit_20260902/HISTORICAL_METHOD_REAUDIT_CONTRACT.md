# Historical DRTP method re-audit contract

Protocol: `HISTORICAL-DRTP-METHOD-REAUDIT-V1`  
Date: `2026-09-02`

## Scope and non-interference

Read-only reclassification of frozen historical result artifacts. No training, rollout, evaluation, checkpoint selection, parameter adjustment, seed replacement, or A-line modification is permitted.

## Comparability unit

Every matrix row is one matched cohort. Its independent unit is the recorded `unit`, never an evaluation episode. Cohorts are never pooled for inference. A method is compared only with its stated frozen comparator, budget, and tape context; results across incompatible arms or horizons are not aggregated.

## Reclassification rules

Primary endpoint: matched robust task return: candidate J_pert_mean minus its frozen comparator.

- `PERFORMANCE_SUCCESS`: within one matched cohort, mean > 0, median > 0, and a strict majority of training-seed (or predeclared ensemble-bundle) effects are > 0.
- `PERFORMANCE_MIXED`: some but not all success conditions hold, or an independent cohort reverses a development-cohort direction.
- `NO_CLEAR_PERFORMANCE_VALUE`: mean <= 0 and median <= 0, or there is no completed matched performance experiment.
- `RELIABILITY_IMPROVED`: requires predeclared lower-tail/catastrophic/dispersion evidence and confirmation in an independent cohort at a comparable horizon.
- `RELIABILITY_MIXED`: a local lower-tail or dispersion improvement is present but lacks independent confirmation or misses another required reliability condition.
- `RELIABILITY_NOT_IMPROVED`: a new catastrophe, larger dispersion, or failed independent reliability gate is observed.

`STABILITY_SOLVED` is deliberately not assigned in this audit: no candidate simultaneously met the required fresh-cohort and comparable-horizon reliability standard. Historical gate decisions are preserved verbatim and are not overwritten by this secondary classification.
