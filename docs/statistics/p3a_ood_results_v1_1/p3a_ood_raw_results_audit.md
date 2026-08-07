# P3-A.3a Raw Results Lock Audit (2026-08-08)

- collection impl tag: `p3a-ood-collection-impl-v1.0` (commit `d26ae6e`)
- protocol: `p3a-ood-protocol-v1.1`, implementation: `p3a-ood-eval-impl-v1.1.3`,
  preflight lock: `p3a-ood-preflight-lock-v1.1`
- run: GPU batch=8, worktree `p3a_ood_collection_v1_0`, PID 9820, exit 0
- raw file: `docs/statistics/p3a_ood_results_v1_1/p3a_ood_raw_results.csv`

## Mechanical audit

| check | result |
|---|---|
| rows | 8400 |
| unique episode keys | 8400 |
| method x seed x cell | 84 cells |
| episodes / cell | 100 |
| missing | 0 |
| duplicate | 0 |
| runtime error | 0 |
| checkpoint SHA empty | 0 |
| exposure violation | 0 |
| tags | protocol/impl/preflight-lock all recorded per row |

Each `method x seed` block = 700 rows = G1 G2 M1 M2 C1 C2 J1 x 100.

## Schema (22 columns)

method, train_seed, cell, episode_id, eval_seed, checkpoint_path,
checkpoint_sha256, checkpoint_update, protocol_tag, implementation_tag,
preflight_lock_tag, steps, failure_start_step, failure_exposed, success,
collision, post_failure_chain_recovered, recovery_window_start_step,
recovery_event_time, censor_time, recovery_observed, reward

Recovery clock is P1-frozen: T_event = recovery_window_start - failure_start
for recovered episodes; T_censor = steps - failure_start otherwise.

## Verdict

> RAW RESULTS LOCK: PASS.
> 8400/8400 complete, unique, no runtime error, no SHA/exposure violation.
> P3-A.3b statistical analysis is now authorized.
