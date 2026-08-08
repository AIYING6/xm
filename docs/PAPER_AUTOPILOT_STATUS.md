# PAPER AUTOPILOT STATUS

## Control and scope

- Control document: `D:/File/Downloads/CODEX_PAPER_AUTOPILOT_MASTER_V7_1_CN_FINAL (1).md` (V7.1-CN FINAL), read on 2026-08-08.
- Language target: Simplified Chinese, journal-neutral manuscript.
- Active production state: `P7_PRE_SUBMISSION_QA`; the evidence-led Chinese intermediate manuscript and its two P1 figures are available, pending submission-metadata and Supplementary packaging.
- Existing active manuscript: `paper_latex_3d_en/main.tex` (English draft; evidence-bearing source only, not the intended final Chinese manuscript).
- Resume source: no earlier `docs/PAPER_AUTOPILOT_STATUS.md` was present.

## Phase register

| Phase | Status | Gate / next output |
|---|---|---|
| P0 Repository & Skill Inspection | COMPLETE | This status, preflight, evidence registry, stale blacklist |
| P1 Evidence Freeze / Preflight | CONDITIONAL PASS | Frozen sources identified; manuscript/data conflicts must be routed before drafting |
| P2 Literature Evidence Layer | COMPLETE | Support, contradiction, closest-work and identity records updated; no novelty-first claim permitted |
| P3 RQ / Claim / Innovation Blueprint | INITIALIZED | Blueprint and hierarchy drafted from project evidence only |
| P4 Statistics & Canonical Paper Data | COMPLETE | Numeric/statistical provenance audits identify RMST80 as P1 and reporting restrictions |
| P5 Figure / Table Contracts | CONDITIONAL PASS | Contracts completed; method figure and Gate Prior figure require remediation before publication |
| P6 Chinese Manuscript Synthesis | COMPLETE | `paper_chinese/manuscript_zh.md` drafted from locked evidence; no line-by-line English translation |
| P7 Figure / Manuscript QA | COMPLETE WITH OPEN PACKAGING ITEMS | Two P1 figures regenerated and visually checked; reviewer-style bounded audit recorded |
| P8 Supplementary Evidence Packaging | INITIALIZED | `paper_chinese/supplementary_zh.md` contains only locked source-data routes and admissible supporting detail |
| P9--P17 | NOT STARTED | Await venue selection, final formatting and submission metadata |

## Current scientific anchor

The newest scientific adjudication is `docs/statistics/p3a_ood_results_v1_1/p3b_halt_decision.md` (commit `12d7a43`, 2026-08-08), read with the P1 survival decision and P3-A statistics lock. The main claim is restricted to earlier post-failure recovery versus MAPPO under the locked nominal held-out distribution; full-horizon recovery is competitive, and zero-shot OOD transfer is distribution-dependent.

## Binding narrative adjudication (2026-08-08)

The accepted paper story is: failure → coordination disruption → post-failure recovery dynamics → task-graph multi-relation coordination → earlier task-level recovery → supporting component evidence → robustness/cost/boundary. The locked nominal KM/RMST evidence remains P1. Full-horizon comparisons, OOD, diagnostics, negative component findings, and stopped P3-B work are not headline contributions. They are routed according to the P1/P2/P3/P4 hierarchy in `PAPER_BLUEPRINT.md` and must not be repeated across Abstract, Results, Discussion, and Conclusion.

No scientific conflict blocks P2--P5. The following are in progress through independent audit lanes: literature evidence; numerical/statistical provenance; and method/figure facts. The Chinese manuscript will be built from their outputs, not translated line-by-line from the existing English draft.

## Completed P2--P5 adjudications

- P2 verified that the paper may claim a specific combination of strict sensing, relay failure, three-relation task representation, and matched-exposure KM/RMST recovery evaluation. It may not claim first use of graph MARL, learned communication, or graph learning for cooperative air combat. Two verified BibTeX corrections were applied to `royston2011rmst` and `zhou2023racer`.
- P4 locks RMST80 versus MAPPO as the P1 time endpoint; it prohibits treating OOD bootstrap probability as a p-value or recovered-only `t_rec` as the main time result. Gate Prior mechanism numbers await a complete audited asset.
- P5 confirms that the method code implements exactly three relations. The current four-relation method schematic is blocked. The current Gate Prior figure is blocked because its Full-with-Prior curve is absent.
- P6 produced the Chinese intermediate manuscript and regenerated the admissible P1 figures: `paper_chinese/figures/fig1_three_relation_task_graph.*` and `fig2_early_recovery_km.*`. Both have provenance files and were visually checked. The Gate Prior trajectory remains excluded.
- P7 records a bounded three-emphasis reviewer audit in `docs/CHINESE_MANUSCRIPT_REVIEW.md`. Its consensus action is packaging and claim discipline, not new training.
- P8 adds a Chinese supplementary draft with seedwise RMST, pre-specified time-window sensitivity, and explicit routes to the locked OOD/robustness/cost assets. The known `hierarchical_bootstrap.csv` early-window `observed_delta` field defect is quarantined in the stale-evidence blacklist; it is not used by the main or supplementary narrative.

## Working-tree protection

At inspection start the repository already contained a modified smoke-test report and many untracked `_tmp_*`, compiled LaTeX, review, and experiment-output artifacts. They are user work / operational artifacts and are not changed or staged by this protocol.

## AUTHOR_DECISION_REQUIRED (non-blocking at P0)

1. Target Chinese journal and its required submission format (Word or LaTeX) are not yet selected.
2. Author, affiliation, funding, conflict, contribution, and data/code availability metadata are absent from the draft.
3. Before final formatting, the author must approve the final journal and any venue-specific AI-use disclosure. No scientific decision is required to begin evidence-led Chinese drafting.
