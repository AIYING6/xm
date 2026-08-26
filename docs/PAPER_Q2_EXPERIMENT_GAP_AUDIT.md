# PAPER-Q2 Experiment Gap Audit

Generated companion: `artifacts/paper_q2/experiment_gap.json`.

No training is authorized in this audit.

## M0 — MUST_HAVE — Claim/provenance alignment
- Status: **COMPLETE_ZERO_TRAINING**
- Requirement: Replace legacy recovery framing and keep development/held-out contracts separate.
## M1 — MUST_HAVE — Seed-level statistics
- Status: **COMPLETE_ZERO_TRAINING**
- Requirement: Report all paired seeds, mean, median, IQR/MAD, worst delta, and contract-stratified summaries.
## M2 — MUST_HAVE — OOD and safety decomposition
- Status: **COMPLETE_IN_MAIN_DRAFT**
- Evidence: The Chinese main draft now shows F0, timing, duration, compound, worst-condition, timeout, collision, constraint, risk-set exposure, task-completion and terminal-outcome evidence from the same 12,000 formal records.
- Boundary: Pre-trigger collisions remain in every unconditional outcome denominator; risk-set exposure is only an evaluator-validity estimand.
## M3 — MUST_HAVE — One strong external comparator
- Status: **COMPLETE_AUDIT — E2 NO_FAIR_EXTERNAL_COMPARATOR**
- Evidence: TAPE and M3DDPG were assessed as scientifically relevant but not fair frozen-contract drop-ins because they change the action/task or learner/information contract.
- Manuscript handling: State this boundary, retain UTR versus DRTP as the primary capacity- and exposure-matched ablation, and do not substitute an incomparable legacy table.
## M4 — HIGH_VALUE — Ablation of DRTP components
- Status: **COMPLETE_FOR_THE_CLAIMED_METHOD_DIFFERENCE**
- Evidence: The main ablation is UTR-SG-MAPPO versus DRTP-SG-MAPPO. Both share the SG backbone, 116,728 parameters, PPO, seven topology groups, fixed 50% nominal anchor, budget and evaluation tape; the sole intervened factor is uniform versus adaptive perturbation weighting.
- Boundary: The nominal anchor is not claimed as a standalone innovation because it is shared. A new removal ablation would be required only if a later manuscript version claims an independent anchor contribution.
## M5 — HIGH_VALUE — Scalability
- Status: **OPEN; NO TRAINING AUTHORIZED**
- Requirement: 4/5-UAV or a defensible scope limitation; use only fair matched protocols.
## M6 — MUST_HAVE — Compute and reproducibility
- Status: **COMPLETE_ZERO_TRAINING**
- Requirement: Report parameter count, training budget, wall-clock provenance where available, inference path, tape hashes, and checkpoint provenance.
## M7 — MUST_HAVE — Prospective common-contract five-seed confirmation
- Status: **COMPLETE — FORMAL_CONFIRMATION_PASS_SEED_SENSITIVE**
- Evidence: paired UTR/DRTP seeds `2301–2305` completed at the common 10M budget and all final checkpoints were evaluated on tape `490000–490099` (12,000 raw records). All five scheduled seeds were retained; no formal catastrophic seed occurred. Historical development/held-out negative evidence remains unchanged.
- Boundary: This closes the prospective matched-comparison gap, not strict unseen-condition OOD, general DRL theory, scalability, HIL, or an adaptive-versus-static-nonuniform causal comparison.
## D0 — DO_NOT_DO — New algorithm search/rescue
- Status: **CLOSED**
- Requirement: No DRTP-v2, SAM-v2, EDR-v2, new encoder, loss, or curriculum.
## D1 — DO_NOT_DO — Post-hoc seed/checkpoint selection
- Status: **PROHIBITED**
- Requirement: Retain seed1902 development limitation and held-out seed2002 reversal.
## D2 — DO_NOT_DO — Universal topology generalization claim
- Status: **CLOSED_BY_G0**
- Requirement: Do not reopen G0 without a new scientific gap and authorization.
