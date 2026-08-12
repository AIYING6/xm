# Phase 2I-A3 strict risk-set root-cause report

**Status:** completed audit; no new training performed  
**Primary classification:** `R2 POLICY IMMATURITY`

## A. Provenance

Branch `scientific_recovery_v2`; baseline tag `PHASE2IA3_RISKSET_AUDIT_BASELINE`; baseline commit `dc37a473be30e27e480e5651a5e5d802ef8e5176`. The audit used only the six Phase 2I-A2 final checkpoints, 1,200 raw validation episodes, manifests, summaries, telemetry, and the endpoint implementation. No canonical seeds `0–4`, canonical test, primary KM/RMST, or new training was used.

## B. Cohort counts

Across all 1,200 episodes: A=1,126, B=22, C=0, D=0, E=52, residual=0. Thus strict risk set `C+D=0`, and strict recovered count `C=0`. The per-arm/seed/scenario machine-readable table is `results/development/phase2ia3_riskset_audit/cohort_counts.csv`.

## C. Endpoint consistency

Strict field mismatch count is 0/1,200. The 50 legacy operational recovery records are documented as a separate semantic discrepancy because they lack strict pre-failure eligibility. Exact timestep reconstruction is limited by the absence of stored per-timestep chain state. There is no evidence sufficient to classify an evaluator implementation bug.

## D. Chain-establishment timing

The retained endpoint proxy shows full_gate has no pre-failure-established episodes in any arm/seed total. no_role_gate has 22 pre-established and maintained episodes in seed 101, and 52 post-failure-first-establishment episodes across seeds. The independent F0 replay found no full_gate chain establishment in 30 episodes; no_role_gate showed only 3 and 1 chain-closed episodes for seeds 101 and 202, respectively, with none for seed 303. This indicates insufficient policy maturity at the 200k-step development budget, not a valid performance comparison.

## E. Failure perturbation

Only 22 episodes were eligible and maintained; zero were eligible-and-lost, so perturbation effectiveness for strict recovery cannot be estimated. R4 is not primary because lack of eligible pre-failure chain dominates. Alternate-path edge timelines were not retained.

## F. Diagnostic feasibility replay

All replay artifacts are labeled `DIAGNOSTIC_FEASIBILITY_ONLY` and stored under `results/development/phase2ia3_riskset_audit/`.

- F0 no-failure: full_gate 0/30 chain-closed episodes; no_role_gate 3/30 for seed 101, 1/30 for seed 202, 0/30 for seed 303.
- F1 delayed failure at fixed step 120: full_gate 0/30 pre-established episodes; no_role_gate 5/10 pre-established for seed 101, 0/10 for seed 202/303, and 1/10 post-failure-first establishment for seed 202.
- No F0/F1 output is a Role-Gate performance result or manuscript evidence.

## G. Gate telemetry

Relation/role-pair stratification is in `stratified_telemetry.csv`. Gate parameters are active and not predominantly saturated; effective payload varies by stratum. This does not resolve efficacy because strict recovery remains unavailable.

## H. Root-cause classification

**Exactly one primary class: `R2 POLICY IMMATURITY`.**

R1 is not supported by the strict consistency audit. R3 is not primary because most policies do not establish a chain even in no-failure replay. R4 cannot be assessed for most episodes because no eligible chain exists to perturb. The evidence is therefore not sufficient to keep or remove Role-Gate.

## I. Minimal next protocol

Do not start it in Phase 2IA3. Review and separately authorize `docs/PHASE2IA4_PROPOSED_PROTOCOL.md`: a larger fixed development budget, same arms/seeds, same strict endpoint, fixed final checkpoint, and pre-registered feasibility/stop rules. Do not resume partial runs, add seeds, alter canonical failure timing, or replace the endpoint with success.

## J. Authorization state

`Role-Gate retention: UNRESOLVED`  
`Final architecture freeze: NO-GO`  
`Phase 3A canonical training: NO-GO`

## Artifact index

- Audit script: `scripts/audit_phase2ia3_riskset_root_cause.py`
- Cohort classification: `results/development/phase2ia3_riskset_audit/episode_cohort_classification.csv`
- Mismatch table: `results/development/phase2ia3_riskset_audit/evaluator_mismatch.csv`
- Timing table: `results/development/phase2ia3_riskset_audit/first_establishment_timing.csv`
- Failure table: `results/development/phase2ia3_riskset_audit/failure_effectiveness_summary.csv`
- Stratified telemetry: `results/development/phase2ia3_riskset_audit/stratified_telemetry.csv`
- Replay manifest: `results/development/phase2ia3_riskset_audit/diagnostic_replay_manifest.json`
