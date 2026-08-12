# Phase 2I-A2 Role-Gate efficacy report

**Artifact class:** `DEVELOPMENT_ONLY`  
**Decision:** `INCONCLUSIVE / ARCHITECTURE FREEZE NO-GO`  
**Date:** 2026-08-12

## Scope and authority boundary

This report closes the frozen Phase 2I-A2 development protocol. It does not use canonical seeds `0–4`, canonical test results, primary survival analysis, headline claims, or checkpoint selection. No endpoint, tau, seed set, failure protocol, or training protocol was changed after formal execution began. Phase 3A remains `NO-GO`.

## A. Provenance

- Branch: `scientific_recovery_v2`.
- Launch tag: `PHASE2IA2_DEVELOPMENT_READY_R1`.
- Development arms: `full_gate` and `no_role_gate`.
- Development seeds: `101`, `202`, `303` only.
- Budget: 782 updates × 4 environments × 64 rollout steps = 200,192 environment steps per arm/seed.
- All six runs completed with 782 logged updates and fixed final checkpoint `actor_critic_latest.pt`.
- No resume, early stopping, seed exclusion, performance-based restart, or checkpoint promotion occurred.
- Training configuration SHA256: `full_gate=2ba851d8657a4d75d68d5f81eff17c61c36b181c7d049881d80325d8872a6eb3`; `no_role_gate=15f856af29c6a70b337c237a8d994b878599853f274dee9beaa533516d43934b`.
- Fixed final checkpoint SHA256 values are recorded in `results/development/role_gate_phase2ia2/manifest.json`; the raw validation SHA256 is `5be3f0661a67b3968b9160ec753d33c0898e2316684c236b52dd038a824b1396`.
- One pre-run launcher incident occurred: host PowerShell lacked `Get-FileHash`. It was corrected with a .NET SHA256 implementation before any run artifact was created; the incident did not discard a completed result or trigger a performance-based rerun.

## B. Completion and validation execution

All required development runs and fixed-checkpoint validations are present:

- 6/6 training runs complete;
- 24 arm × seed × scenario validation rows;
- 12 paired arm-comparison rows;
- 50 episodes per arm × seed × scenario;
- deterministic development IDs follow `210000 + 10000 × seed + 1000 × scenario_index + episode_index`;
- raw episode metrics, per-seed summaries, per-scenario summaries, arm comparisons, telemetry, and manifest are present.

The validation used only the fixed final checkpoint. No KM/RMST or canonical statistical result was generated.

## C. Gate-learning evidence

| full_gate seed | gate-gradient mean | final | displacement mean | final | gate mean | gate SD |
|---:|---:|---:|---:|---:|---:|---:|
| 101 | 3.7391e-4 | 4.0031e-4 | 0.2984 | 0.4553 | 0.4348 | 0.0477 |
| 202 | 3.5999e-4 | 2.2015e-4 | 0.2155 | 0.3497 | 0.4341 | 0.0472 |
| 303 | 5.3366e-4 | 8.8310e-4 | 0.2469 | 0.5234 | 0.4348 | 0.0476 |

All three seeds have finite non-zero gate gradients and non-zero material displacement. The aggregate gate variation is modest but non-zero; this is evidence of optimization activity, not sufficient evidence of useful architectural contribution. Relation/role-pair telemetry is present for all full-gate runs.

## D. Attention compensation diagnostic

| full_gate seed | corr(alpha, g) | effective payload mean | telemetry rows |
|---:|---:|---:|---:|
| 101 | 0.5553 | 0.2393 | 10,824 |
| 202 | 0.5745 | 0.2393 | 11,269 |
| 303 | 0.6156 | 0.2432 | 10,706 |

The observed positive, moderate `corr(alpha, g)` does not support a simple inverse-attention compensation explanation. However, these are pooled telemetry correlations, not a causal or relation-stratified proof that the gate contributes unique decision value. The effective-payload diagnostic therefore passes only as a limited diagnostic and cannot rescue an unestimable validation endpoint.

## E. Development-only validation findings

The strict endpoint was applied exactly as frozen. The strict risk-set size was **zero in every arm × seed × scenario row**.

- `full_gate`: seed 101/202/303 each had 0 pre-failure established episodes, 200 post-failure loss records across four scenarios, strict risk set 0, and recovered count 0.
- `no_role_gate`: seed 101 had 22 pre-failure established episodes across four scenarios; seeds 202 and 303 had 0. Nevertheless, every row had strict risk set 0 and recovered count 0.
- Consequently, strict recovery probability, conditional recovery time, `t_loss`, `t_recovery`, and `delta_t_loss_to_recovery` are all `NaN`/not estimable for the formal comparison.
- Operational success/timeout fields are retained as diagnostics only. They cannot substitute for the pre-registered strict recovery diagnostic and are not a manuscript claim.

This is an evidence-availability failure for the frozen validation suite, not permission to redefine the endpoint or rerun favorable seeds.

## F. Pre-registered retention-rule matrix

| Rule | Result | Basis |
|---|---|---|
| 1. Finite non-zero gradients and material displacement in each seed | `PASS` | All full-gate seeds satisfy both conditions. |
| 2. No predominant saturation and relation/role differentiation | `PARTIAL / NOT SUFFICIENT` | Non-zero gate variation and telemetry are present; available aggregate telemetry does not establish a complete, decision-sufficient differentiation test. |
| 3. Effective payload not solely explained by inverse attention response | `PARTIAL PASS` | Pooled correlations are positive/moderate; diagnostic is limited, not causal. |
| 4. Full gate not worse on fixed recovery diagnostics while stable | `NOT ESTIMABLE` | Strict risk set is zero for every row; recovery diagnostics are all unavailable. |

The four-condition conjunction is therefore not satisfied and cannot be resolved by selecting endpoints, seeds, or checkpoints.

## G. Final decision

**INCONCLUSIVE / ARCHITECTURE FREEZE NO-GO.**

This is the single allowed conclusion for the observed mixed/unevaluable development evidence. Do not claim `KEEP ROLE-GATE` or `REMOVE ROLE-GATE`, do not declare the architecture frozen, and do not start Phase 3A or canonical training. The appropriate next action is a separately authorized protocol-level investigation of why the fixed development suite produces zero strict risk sets; that investigation must be documented before any new evaluation or training and must not silently alter the frozen protocol.

## H. Current project state

- Development executor: implemented and completed.
- Six DEVELOPMENT_ONLY runs: complete.
- Fixed-final-checkpoint validation: complete.
- Role-Gate retention: unresolved.
- Final architecture freeze: `NO-GO`.
- `CANONICAL_V2_TRAINING_READY` tag: not created.
- Phase 3A formal training: `NO-GO`.

## Artifact index

- Protocol: `docs/PHASE2IA2_ROLE_GATE_EFFICACY_PROTOCOL.md`
- Completion audit: `docs/PHASE2IA2_TRAINING_COMPLETION_AUDIT.md`
- Validation manifest: `results/development/role_gate_phase2ia2/manifest.json`
- Raw validation: `results/development/role_gate_phase2ia2/raw_validation/episode_metrics.csv`
- Summaries: `results/development/role_gate_phase2ia2/summaries/`
- Telemetry: `results/development/role_gate_phase2ia2/telemetry/`
