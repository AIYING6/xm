# Proposed Phase 2I-A4 development protocol

**Status: proposal only; not authorized.**

Primary cause from Phase 2I-A3: `R2 POLICY IMMATURITY`. The existing 200,192-step policies are not sufficiently capable of establishing the chain before failure for an estimable strict recovery comparison. No new run is authorized by this document.

Before any Phase 2I-A4 run, separately freeze:

- the same two arms: `full_gate` and `no_role_gate`;
- development seeds `101/202/303` unless a future protocol explicitly changes them;
- a larger fixed training budget selected before inspecting outcomes;
- identical training and evaluation conditions for both arms;
- the frozen strict recovery endpoint unchanged;
- a fixed validation suite and deterministic episode-ID rule;
- fixed final checkpoint only, with no resume, early stopping, seed exclusion, or checkpoint promotion;
- telemetry, cohort, evaluator-consistency, and stop rules;
- explicit feasibility criteria for pre-failure chain establishment before any retention comparison.

The proposal must be reviewed and authorized separately. It must not reuse partial training or silently substitute operational success for the strict endpoint.
