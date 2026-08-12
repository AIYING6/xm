# Phase 2I-A4 pre-result V0 risk-set adequacy rule

**Status:** frozen before Phase 2IA4 validation outcomes.

V0 is assessed separately for each arm × development seed × frozen scenario, then aggregated by arm and seed. V0 passes only if all conditions hold:

1. Both arms have a non-zero strict risk set (`C + D`).
2. In each arm, strict-risk-set episodes occur in at least two of the three development seeds.
3. In each arm, strict-risk-set episodes occur in at least two of the four frozen scenarios.
4. In each arm, total strict-risk-set episodes across the validation suite are at least 40.
5. In each arm, at least two seeds each contribute at least 10 strict-risk-set episodes.

The rule is applied to independently reconstructed timestep-level cohorts. `success`, operational recovery, return, timeout, or any secondary endpoint cannot satisfy V0. If any condition fails, the result is:

`ROLE-GATE EFFICACY = NOT ESTIMABLE DUE TO RISK-SET FAILURE`

and:

`ARCHITECTURE FREEZE = NO-GO`.

This threshold is fixed before validation and cannot be changed after inspecting outcomes.
