# DRTP final-paper closure workspace

This directory contains paper-preparation assets that do not train, evaluate, select checkpoints, or read a running cloud job. It is intentionally separated from generated `results/` artifacts.

## Frozen paper argument

In heterogeneous UAV coordination under topology perturbations, Original DRTP adaptively reallocates training exposure across the frozen failure-condition groups. Its primary supported result is a repeated *cohort-level mean robustness benefit* relative to the matched UTR control in two independently seeded 10M cohorts. The paper does not claim universal per-seed superiority.

## Evidence status

| Evidence block | Status | Paper role |
|---|---|---|
| Matched UTR/DRTP, cohort A and B | complete | Main robustness evidence |
| Held-out / OOD endpoint evaluation | complete | Generalization evidence |
| PLR-style matched external comparator | running | External adaptive-sampling comparison |
| Six-UAV cross-scale UTR/DRTP run | running | Cross-scale evidence |

The two running blocks must be incorporated only after their fixed endpoints and manifests are complete. No training-time measurement may be used as a final result.

## Contents

- `DRTP_FINAL_STATISTICAL_ANALYSIS_PLAN.md`: fixed reporting and aggregation rules.
- `DRTP_FINAL_FIGURE_CONTRACT.md`: figure logic, evidence roles, and source-data requirements.
- `DRTP_FINAL_MANUSCRIPT_SCAFFOLD.md`: English paper structure and claim boundaries.
- `DRTP_FINAL_TERMINOLOGY_LEDGER.md`: canonical terminology.
- `scripts/plot_drtp_final_cohort_pairs.py`: Python-only seed-level paired figure generator.

