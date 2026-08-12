# Phase 2I-A3 endpoint implementation audit

## Result

Strict endpoint mismatch count: **0 / 1,200** under the available episode-level fields. The frozen strict event is consistent with:

`pre_failure_chain_established AND chain_lost_after_failure AND post_failure_chain_recovered_after_loss`.

The audit therefore does **not** classify the zero risk set as `R1 EVALUATOR BUG`.

## Legacy operational-field discrepancy

Fifty `no_role_gate`, seed 101 records contain a legacy operational `t_recovery`/`post_failure_chain_recovered` indication while `pre_failure_chain_established=0`, `post_failure_chain_recovered_after_loss=0`, and `event=0`. This is a semantic difference between an operational post-failure detector and the strict endpoint, not a strict endpoint error. Those episodes are Cohort E, not strict events.

The discrepancy is preserved in `evaluator_mismatch.csv` as `operational_semantic_discrepancy`; no field was rewritten and no result was promoted to strict recovery.

## Independent reconstruction limitation

Phase 2I-A2 retained endpoint summaries but not timestep-level `C_t` trajectories. Therefore an exact independent per-timestep timeline cannot be reconstructed retrospectively. The Phase 2IA3 script records this limitation in every classification row and uses only frozen fields for the cohort identity checks.
