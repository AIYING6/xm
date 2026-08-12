# Canonical protocol amendment: B1 timing

**Amendment ID:** `B1-TIMING-V1`  
**Branch:** `scientific_recovery_v2`  
**Timing:** submitted before any canonical Phase 3A formal result was observed  
**Scope:** launch-gate timing only

## Decision

Gate B1 is moved from a pre-training gate to a pre-headline-analysis gate.

Formal canonical training may begin when Gate A1 = PASS, Gate H = CLOSED, and Gate C0 = PASS. Gate B1 must pass before any canonical KM curve, RMST value, hierarchical-bootstrap survival contrast, or manuscript headline survival number is promoted or interpreted as headline evidence.

## Invariants

This amendment does not change any scientific protocol or data-generating rule. The following remain frozen:

- strict recovery endpoint: `pre_failure_chain_established AND chain_lost_after_failure AND post_failure_chain_recovered_after_loss`;
- primary recovery duration: `t_recovery - t_loss`;
- primary tau: `80`;
- sensitivity taus: `50, 80, 100, 150, 190, 220`;
- censoring and cohort rules;
- seed set: exactly `0, 1, 2, 3, 4`;
- training budget and validation-only checkpoint selection;
- four method identities and scenario definitions;
- reward, failure timing, observation, communication, sender/receiver, and recovery semantics.

Raw episode generation and non-headline descriptive checks may proceed. Until B1 passes, canonical survival outputs remain analysis-blocked. No formal result observed after this amendment may be used to revise the endpoint, tau, seed set, failure protocol, or checkpoint policy.

## Independent B1 route

B1 will be resolved independently on a clean CI runner using a standard survival implementation, normal TLS verification, the frozen synthetic matrix, all frozen taus, and the empirical-format fixture when canonical empirical data are not yet available. Package/version, runner, input/output hashes, errors, and tolerance will be preserved in `analysis/survival_v2/STANDARD_REFERENCE_CROSS_VALIDATION_V3.md`.

## Approval condition

This amendment authorizes Phase 3A training only under the pre-training gates above. It does not itself declare B1 PASS and does not authorize headline survival interpretation.
