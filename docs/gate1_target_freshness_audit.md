# Gate 1 Target-Message Freshness Audit

Last updated: 2026-07-18

## Scope

This pass hardens the strict-sensing bottleneck so delivered target messages cannot remain valid forever.

The change is part of Gate 1 information-realism hardening. It does not convert earlier five-seed results into final paper evidence; formal results must be rerun after all P0 fixes are complete.

## Implemented

- Added `max_target_message_age_steps` and `min_target_confidence` to the 3DOF environment and RI-GMAPPO configuration.
- Propagated both fields through training, BC pretraining, evaluation, checkpoint sweep, formal protocol, topology robustness, geometric baseline, replay, and mechanism-analysis scripts.
- `_has_target_information()` now accepts direct sensing or a fresh target cache, but rejects stale or low-confidence cache entries.
- Attacker chain checks now inherit the same freshness semantics through `_has_target_information()`.
- Actor local target-cache confidence returns `0.0` when the cache is stale or below confidence threshold.
- Exported environment info now includes `target_cache_age_mean`, `target_cache_confidence_mean`, and `target_cache_stale_rate`.

## Tests

Added Gate 1 regression coverage for:

- stale target cache cannot close the attacker chain;
- low-confidence target cache cannot close the attacker chain;
- fresh target cache remains valid;
- stale cache confidence is hidden from actor observation.

Verification run:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe -m py_compile ...
D:/Anaconda/envs/.conda/envs/cac/python.exe -m unittest tests.test_gate1_communication_feasibility
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/smoke_test_intercept_3d_env.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_ri_gmappo_3d.py --allow-random-policy --episodes 1 --strict-target-sensing --agent-target-info-bottleneck --max-target-message-age-steps 5 --min-target-confidence 0.2 ...
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/evaluate_3d_geometric_node_failure.py --seeds 0 --episodes 1 --scenarios relay_failure --strict-target-sensing --agent-target-info-bottleneck ...
```

Observed result:

```text
py_compile: pass
Gate 1 unit tests: 11 tests OK
3DOF environment smoke: 15 episodes OK
freshness evaluator smoke: pass
freshness geometric CSV smoke: pass
```

## Remaining Gate 1 P0 Items

- Define one pre-step/post-step convention for `step`, message delivery, node failure, and metric logging.
- Add boundary tests for failure start/end and delayed message delivery.
- Split post-failure outcomes into maintained, recovered, and unrecovered instead of relying only on a recovered flag.
- Replace remaining actor-side graph target shortcuts with packet/ego-consistent graph information.

