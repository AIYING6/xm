# PAPER-Q2 Complete Asset Ledger

Generated machine-readable companion: `artifacts/paper_q2/asset_ledger.json`.

## Classification rules

- **MAIN_TEXT:** contract-matched and directly supports the frozen DRTP claim.
- **SUPPLEMENTARY:** useful negative, mechanism, or audit evidence but not the headline result.
- **INTERNAL_ONLY:** historical planning or superseded material.
- **INVALID_NON_COMPARABLE:** not allowed in the current evidence chain because estimands/contracts differ.

## Ledger

### S1/S1B/S2 problem and mechanism freeze
- Classification: **MAIN_TEXT**
- Contract: S2 frozen
- Status: reusable
- Sources: `docs/PHASE_S1B_TOPOLOGY_RECONFIGURATION_VALIDATION_REPORT.md`, `docs/PHASE_S2_FINAL_FREEZE_REPORT.md`, `docs/PHASE_S2_CLAIM_EVIDENCE_BOUNDARY.md`
- Notes: Supports relay-node-induced topology/path reconfiguration; not information-loss or recovery.
### T1 clean UTR five-seed reference
- Classification: **MAIN_TEXT**
- Contract: T1 1M, seeds 2201-2205
- Status: reusable
- Sources: `docs/T1_TELEMETRY_NATIVE_REFERENCE_REPORT.md`, `docs/T1_SEED_LEVEL_REFERENCE_AND_RANKING.md`, `results/development/t1_telemetry_native_reference_1m_run1`
- Notes: Clean baseline reference; descriptive, not a universal superiority claim.
### DRTP paired historical audit
- Classification: **MAIN_TEXT**
- Contract: development_3M + heldout_10M, separate contracts
- Status: reusable_with_boundary
- Sources: `docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.md`, `docs/DRTP_Q2_PUBLICATION_VIABILITY_AUDIT.json`, `docs/DRTP_Q2R_ZERO_TRAINING_FAIR_REVIEW.md`
- Notes: Report development and held-out sets separately; never pool them as one homogeneous experiment.
### DRTP held-out final evidence
- Classification: **MAIN_TEXT**
- Contract: v2 held-out 10M, seeds 2001-2003
- Status: reusable_with_negative_result
- Sources: `docs/DRTP_HELDOUT_V2_AUDIT_REPORT.md`, `docs/DRTP_HELDOUT_FAILURE_FORENSIC_REVIEW.md`
- Notes: Must retain seed2002 reversal and overall held-out FAIL.
### FL failure learnability upper bound
- Classification: **SUPPLEMENTARY**
- Contract: FL maturity 1M, seeds 1801-1802
- Status: reusable_for_limitation
- Sources: `docs/PHASE_FL_TRAINING_MATURITY_UPPER_BOUND_REPORT.md`
- Notes: Shows F0 can be learned by a specialist; not a main method comparison.
### G0 unseen topology generalization audit
- Classification: **SUPPLEMENTARY**
- Contract: zero-training diagnostic
- Status: reusable_for_limitation
- Sources: `docs/G0_FINAL_DECISION.md`, `docs/G0_ZERO_SHOT_RESULTS.md`, `docs/G0_GENERALIZATION_GAP_ANALYSIS.md`
- Notes: Decision C; do not claim a universal topology-generalization gap.
### TC-SAM / EDR / TCR / SPC / CTP negative evidence
- Classification: **SUPPLEMENTARY**
- Contract: historical development contracts
- Status: reusable_as_negative_evidence
- Sources: `docs/TC_SAM_D1_FINAL_DECISION.md`, `docs/EDR_D1_FINAL_DECISION.md`, `docs/TCR_SPC_PHASE_C_V2_REANALYSIS_REPORT.md`, `docs/DRTP_SG_MAPPO_DEVELOPMENT_PERFORMANCE_REPORT.md`
- Notes: Do not use to inflate method count or imply a selective benchmark.
### Old EA-RG / multi-relation paper draft
- Classification: **INVALID_NON_COMPARABLE**
- Contract: legacy recovery paper
- Status: do_not_reuse_claims
- Sources: `paper_latex_3d_en/main.tex`, `paper_latex_3d_en/README.md`, `docs/PAPER_CODE_EQUIVALENCE_AUDIT_V3.md`
- Notes: Claims recovery, old Full, and old metrics incompatible with frozen DRTP problem/claim boundary.
### Gate1 safety/fx60 paper tables
- Classification: **INVALID_NON_COMPARABLE**
- Contract: legacy recovery/fx60 table contract
- Status: do_not_mix
- Sources: `results/gate1_safety_fx60_paper_tables/main_results.csv`, `results/gate1_safety_fx60_paper_tables/ablation_results.csv`, `results/gate1_safety_fx60_paper_tables/capacity_control_results.csv`, `results/gate1_safety_fx60_paper_tables/seed_aware_deltas.csv`
- Notes: Uses recovery/chain metrics and old method labels; not commensurate with T1/DRTP frozen estimands.
### Old M0 TC-SAM positioning/feasibility
- Classification: **INTERNAL_ONLY**
- Contract: superseded
- Status: historical_only
- Sources: `docs/M0_Q2_PAPER_POSITIONING.md`, `docs/M0_OFFLINE_FEASIBILITY.md`
- Notes: Superseded by DRTP positioning and should not be cited as current method definition.

## Frozen historical decisions

DRTP development `NO-GO`, DRTP held-out `FAIL`, TC-SAM `DEV_FAIL`, EDR `DEV_FAIL`, and G0 `NO_ACTIONABLE_TOPOLOGY_GENERALIZATION_GAP` are retained. No negative result is deleted or rewritten.
