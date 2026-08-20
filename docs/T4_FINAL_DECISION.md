# T4 Final Decision

## Frozen decision

**U1 — SUPPORT_UTILIZATION_GAP_IDENTIFIED**

T4 provides convergent zero-training evidence that the existing good and weak UTR/SG seeds respond differently to recorded, actor-legal task-support state:

- Good minus weak failure sensitivity is `+0.283` for the unavailable/stale mask probe and `+0.100` for the within-stratum recorded-value permutation control.
- The good-minus-weak sensitivity gap grows from `+0.145` before failure onset to `+0.322` in the early topology-perturbation phase.
- Sensitivity aligns descriptively with `J_F0`, `J_OOD_mean`, and `J_OOD_worst` at Spearman `+0.80` across the five fixed seeds.
- The latent probe shows that weak seeds are not simply missing decodable support-related state; the evidence is more consistent with differing utilization of available legal information.

## What this decision permits and forbids

This is a mechanism-discovery result, not a method result. It does not authorize a new network, loss, optimizer, training run, curriculum, environment change, held-out evaluation, or canonical evaluation. It does not override the permanently frozen T3 `D — NO_GO` temporal-memory/continuity route.

Any future work must begin with a separately authorized design review that tests whether this frozen-policy utilization gap yields a distinct, offline-verifiable and scientifically necessary intervention. T4 itself ends here.

## Provenance

- Protocol: `T4-SUPPORT-UTILIZATION-GAP-AUDIT-V1`
- Inputs: five frozen T1 final checkpoints and native telemetry only
- Output: `results/development/t4_support_utilization_audit_run1/t4_utilization_audit.json`
- Environment interaction / optimizer updates: none
