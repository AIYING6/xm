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
- Status: **COMPLETE_AUDIT; PRESENTATION_REQUIRED**
- Requirement: Show F0, timing, duration, compound, worst condition, timeout, collision, constraints, exposure.
## M3 — MUST_HAVE — One strong external comparator
- Status: **OPEN; NO TRAINING AUTHORIZED**
- Requirement: Assess whether a directly relevant robust/topology-aware MARL comparator can be implemented under a separately frozen contract; do not substitute an incomparable legacy table.
## M4 — HIGH_VALUE — Ablation of DRTP components
- Status: **OPEN; NO TRAINING AUTHORIZED**
- Requirement: Uniform topology training, nominal anchor, and adaptive weighting ablations only if a new contract is separately authorized.
## M5 — HIGH_VALUE — Scalability
- Status: **OPEN; NO TRAINING AUTHORIZED**
- Requirement: 4/5-UAV or a defensible scope limitation; use only fair matched protocols.
## M6 — MUST_HAVE — Compute and reproducibility
- Status: **COMPLETE_ZERO_TRAINING**
- Requirement: Report parameter count, training budget, wall-clock provenance where available, inference path, tape hashes, and checkpoint provenance.
## D0 — DO_NOT_DO — New algorithm search/rescue
- Status: **CLOSED**
- Requirement: No DRTP-v2, SAM-v2, EDR-v2, new encoder, loss, or curriculum.
## D1 — DO_NOT_DO — Post-hoc seed/checkpoint selection
- Status: **PROHIBITED**
- Requirement: Retain seed1902 development limitation and held-out seed2002 reversal.
## D2 — DO_NOT_DO — Universal topology generalization claim
- Status: **CLOSED_BY_G0**
- Requirement: Do not reopen G0 without a new scientific gap and authorization.
