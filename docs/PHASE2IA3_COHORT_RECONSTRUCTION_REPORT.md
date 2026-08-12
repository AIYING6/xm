# Phase 2I-A3 cohort reconstruction

## Scope

The 1,200 existing Phase 2I-A2 episode records were classified using the frozen strict endpoint. The raw artifact is episode-level and does not contain timestep-by-timestep chain state, so exact independent timeline reconstruction is not possible from this artifact; the limitation is recorded rather than imputed.

## Cohort totals

| Cohort | Definition | Count |
|---|---|---:|
| A | Never pre-established | 1,126 |
| B | Pre-established and maintained after failure | 22 |
| C | Pre-established, lost, recovered | 0 |
| D | Pre-established, lost, not recovered | 0 |
| E | First establishment only after failure | 52 |
| Residual/invalid | Explicitly documented | 0 |

The identity `total = A+B+C+D+E+residual` holds for every arm × seed × scenario aggregation. The reconstructed strict risk set `C+D` is zero and strict recovered count `C` is zero in every aggregation.

## Per-arm/seed totals

| Arm | Seed | A | B | C | D | E | Strict risk set |
|---|---:|---:|---:|---:|---:|---:|---:|
| full_gate | 101 | 200 | 0 | 0 | 0 | 0 | 0 |
| full_gate | 202 | 200 | 0 | 0 | 0 | 0 | 0 |
| full_gate | 303 | 200 | 0 | 0 | 0 | 0 | 0 |
| no_role_gate | 101 | 160 | 22 | 0 | 0 | 18 | 0 |
| no_role_gate | 202 | 167 | 0 | 0 | 0 | 33 | 0 |
| no_role_gate | 303 | 199 | 0 | 0 | 0 | 1 | 0 |

Machine-readable classifications and all arm × seed × scenario counts are in `results/development/phase2ia3_riskset_audit/episode_cohort_classification.csv` and `cohort_counts.csv`.
