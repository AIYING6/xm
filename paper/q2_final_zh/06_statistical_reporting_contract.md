# 06 Statistical Reporting Contract

## Design and independent unit

The independent unit for method comparison is the **training seed**. Evaluation episodes quantify the performance of a trained policy within a condition; they are not independent training replicates and shall not be used to inflate `n`.

## Contract strata

| Stratum | Training seeds | Budget | Permitted use |
|---|---:|---:|---|
| development | 1901, 1902 | 3M | descriptive development evidence only |
| held-out v2 | 2001, 2002, 2003 | 10M | held-out evidence with historical `FAIL` retained |
| prospective formal confirmation | 2301, 2302, 2303, 2304, 2305 | 10M | primary homogeneous five-seed evidence; result pending |

The historical strata differ in training budget and evaluation contract. They must be shown separately before any retrospective five-pair summary. That historical summary is a descriptive reliability audit, not one homogeneous confirmatory experiment. By contrast, the prospective formal stratum is one frozen, homogeneous five-seed experiment and is the primary unit for the final method decision.

## Required reporting per primary metric

For `J_nominal`, `J_F0`, `J_OOD_mean`, and `J_OOD_worst`, report:

- absolute UTR and DRTP values within each contract and seed where available;
- paired `DRTP − UTR` differences;
- win count;
- mean and median paired differences;
- sample SD, IQR, MAD, and worst paired degradation;
- all individual seed points;
- descriptive bootstrap interval only when explicitly labeled descriptive.

## Statistical interpretation

- No episode-pooled p value may be used for a method-superiority claim.
- No formal population-level superiority claim is justified by the mixed-contract `n=5` retrospective summary.
- The seed-level bootstrap interval is descriptive and does not repair the contract heterogeneity.
- A positive mean or median does not establish stability.
- Seed1902 and seed2002 must remain visible adjacent to the central performance claim.
- Safety outcomes must be reported separately from return metrics.
- Risk-set trigger validity is an evaluator quantity; pre-trigger collision remains an unconditional policy safety/performance outcome.
- The prospective formal report must include catastrophic-seed count, paired direction for every seed, safety differences, pre-trigger collision, survival-to-onset fraction, and risk-set trigger validity.
- Live logs, incomplete method pairs, and intermediate checkpoints are not admissible manuscript evidence.

## Missing-data and exclusion policy

No completed seed is excluded for weak performance. No checkpoint promotion is allowed. Missing per-seed development timeout values shall remain `NA`; they must not be imputed from pooled or condition-level values.

## Machine sources

- `final_paired_absolute_results.csv` — 10 method×seed absolute rows;
- `final_seed_level_results.csv` — five paired seed rows;
- `final_reliability_results.csv` — recomputed five-pair descriptive statistics;
- `final_stratified_statistics.csv` — separate `n=2` and `n=3` summaries;
- `evidence_chain_audit.json` — machine verification status.

## Reviewer-facing boundary

The defensible statistical conclusion is:

> Historical paired evidence has a positive mean and median center for all four return metrics, but the small, contract-separated seed sets and severe adverse seed preclude a seed-stable or generally reliable superiority claim.
