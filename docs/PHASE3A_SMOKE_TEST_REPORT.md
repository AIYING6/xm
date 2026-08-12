# Phase 3A engineering smoke-test report

**Status:** PASS — engineering-only; not scientific evidence  
**Artifact class:** `ENGINEERING_SMOKE_TEST_ONLY`  
**Formal training observed before this report:** No

## Scope

All four frozen Phase 3A method identities were exercised in the 3DOF environment with one tiny update and one evaluation episode:

| Method | Graph configuration | Residual weight | Result |
|---|---|---:|---|
| `EA-RG-MAPPO-S` | `multi_relation` | 1.0 | PASS |
| `MAPPO` | `no_graph` | 1.0 | PASS |
| `Single-Graph` | `single` | 1.0 | PASS |
| `EA-RG-MAPPO-S-no-union-residual` | `multi_relation` | 0.0 | PASS |

## Checks passed

- 3DOF training runner starts and completes one update for all four identities.
- Checkpoint bytes are written for every method and SHA256 values are recorded in `results/canonical_v2/smoke/smoke_manifest.json`.
- Validation/evaluation starts from the saved checkpoint for every method.
- Raw episode CSVs are generated.
- Required v2 fields are present, including `pre_failure_chain_established`, `chain_lost_after_failure`, `t_failure`, `t_loss`, `post_failure_chain_recovered_after_loss`, `t_recovery`, `delta_t_loss_to_recovery`, `post_failure_chain_first_established`, `event`, and `censor_time`.
- Method identity is passed explicitly to the evaluator; it is not inferred from a filename.

## Boundary

The smoke outputs are not canonical results, are not used for checkpoint selection, and are not used for paper claims. Their success only establishes that the frozen pipeline can start, save, reload, evaluate, and emit the required schema. Formal Wave 1 remains fixed to seeds 0–4 and the pre-registered budget/protocol.
