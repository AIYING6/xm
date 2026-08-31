# Reliable-DRTP ensemble P1 technical preflight

**Verdict:** RELIABILITY_ENSEMBLE_P1_PREFLIGHT_FAIL.

This preflight uses synthetic logits only. It loads no experiment checkpoint, creates no environment, starts no rollout/evaluation/training, and does not implement distillation.

## Interface checks

- PASS — one_member_probability_equivalence
- PASS — one_member_deterministic_action_equivalence
- PASS — pooled_simplex
- PASS — pooled_nonnegative
- PASS — member_order_invariance
- PASS — pooled_action_shape
- PASS — member_shape_rejection

## Candidate seed audit

- Candidate seeds: 4601–4619
- Text files scanned: 1100
- Identifier hits: {'4602': ['paper/q2_final_zh/formal_results/source_data/evaluation_manifest.json'], '4603': ['docs/DRTP_MAPPO_EXTERNAL_BASELINE_TRAINING_CONTRACT.md', 'docs/DRTP_MAPPO_EXTERNAL_REFERENCE_AUDIT.md', 'docs/DRTP_UTR_Q2_FORMAL_EXECUTION_READINESS_REPORT.md', 'paper/q2_final_en/11_supplementary_information.md', 'paper/q2_final_zh/14_formal_result_integration_audit.md', 'paper/q2_final_zh/24_anonymous_reproducibility_package.md', 'paper/q2_final_zh/25_final_evidence_manifest.json', 'paper/q2_final_zh/main_zh.md', 'paper/q2_final_zh/formal_results/external_reference_summary.md', 'paper/q2_final_zh/formal_results/integration_manifest.json', 'paper/q2_final_zh/formal_results/source_data/DRTP_UTR_Q2_FORMAL_DECISION.json', 'paper/q2_final_zh/formal_results/source_data/evaluation_manifest.json', 'paper/q2_final_zh/formal_results/source_data/formal_tape_manifest.json', 'paper/q2_final_zh/supplementary/S3_hyperparameters_projection_and_provenance.md', 'paper/q2_final_zh/supplementary/source_data/snr_independent_replication/evaluation_manifest.json', 'scripts/check_q2_final_zh_manuscript.py', 'scripts/integrate_drtp_utr_q2_formal_results.py', 'scripts/run_drtp_cross_tape_reliability.py', 'scripts/run_drtp_mappo_external_evaluation.py', 'scripts/verify_drtp_mappo_external_contract.py'], '4608': ['docs/drtp_stabilization_s0/s0_q_update_movements.csv'], '4610': ['paper/q2_final_zh/supplementary/source_data/snr_independent_replication/evaluation_manifest.json'], '4613': ['docs/DRTP_REL_A0_FINAL_REPORT.md'], '4614': ['paper/q2_final_zh/supplementary/source_data/snr_independent_replication/evaluation_manifest.json'], '4615': ['docs/EGTR_P3_1M_TRAINING_COMPLETION_AUDIT.md']}

This is not a final cloud provenance decision. The execution launcher must re-audit archived run manifests and supplied assets before any training starts.

## Stop boundary

A pass means only that the default-off pooling primitive and preliminary source registry are ready. It does not authorize P1 member training, E-DRTP evaluation, distillation, K selection, member selection, or any continuation.
