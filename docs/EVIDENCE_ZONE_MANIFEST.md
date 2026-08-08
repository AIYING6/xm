# Evidence Zone Manifest

## Tier A — current controlling decisions (read-only for scientific content)

| Source | Authority | Use |
|---|---|---|
| `docs/statistics/p3a_ood_results_v1_1/p3b_halt_decision.md` | newest explicit decision, 2026-08-08 | paper scope; OOD boundary; P3-B exclusion |
| `docs/statistics/p3a_ood_results_v1_1/p3a_ood_stats_lock_memo.md` | frozen OOD verdict | OOD quantitative boundary only |
| `docs/statistics/P1B_DECISION_MEMO_V1_1.md` | survival headline adjudication | primary claim ceiling |
| `docs/P0_PROVENANCE_LOCK_V1_6_PROPOSED.md` | v1.6 provenance lock | supersession and component wording |

## Tier B — canonical formal evidence (read-only)

| Source | Authority | Use |
|---|---|---|
| `docs/statistics/survival_results_v1_1/` | locked held-out survival outputs | RMST/KM/statistical reporting |
| `docs/paper_assets_v1_5/canonical_results_v1_5.csv` | numeric source for v1.5 held-out, ablation, robustness, efficiency tables | programmatic tables and non-survival results |
| `docs/paper_assets_v1_5/consistency_audit_v1_5.md` | canonical table consistency | numeric cross-check |
| `results/claim_evidence_matrix.csv` and `docs/claim_evidence_matrix.md` | claim linkage | historical aid; reconcile against v1.6 before reuse |
| `docs/statistics/p3a_ood_results_v1_1/p3a_ood_raw_results.csv` | locked raw OOD episodes | only via frozen analysis protocol |

## Tier C — implementation truth

`envs/uav_intercept_3d_env.py`, `algorithms/ri_gmappo/simple_ri_gmappo.py`, `configs/paper/*.yaml`, evaluation scripts, and P3-A scripts define what the locked experiments actually implement. The method/code firewall requires tracing any new Method sentence to these files.

## Tier D — historical, development-only, or uncertain

- Early 2D EA-RG-MAPPO-S outputs and July status summaries.
- Fixed-update-60/five-seed Gate-1 assets (`results/gate1_safety_fx60_paper_tables/`) when they conflict with the newer v1.6, 3-seed survival state.
- P3-B calibration drafts/infrastructure: archived future-work only.
- `_tmp_*`, operator notes, scratch scripts, `.aux/.bbl/.blg`, and untracked PDF: not manuscript evidence.
- `docs/paper_assets_v1_5/paper_review_v1_6.md`: useful editorial diagnostic, but currently untracked and not scientific evidence.
