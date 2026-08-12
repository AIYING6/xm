# Scientific Upgrade Phase 2 Report

Generated: 2026-08-12

Scope: Phase 2A–2F evidence repair only. No training was started, no training protocol was changed, and no new headline survival number was introduced.

## Phase 2A — Historical evidence recovery

Recovered into archival-only storage:

- 5-seed formal raw test episode CSVs;
- merged and per-seed selected-test summaries;
- validation episode/checkpoint-selection artifacts;
- formal protocol and training logs;
- historical survival v1.1 protocol and derived outputs;
- historical robustness/OOD candidate CSVs;
- baseline identity manifest with config SHA256 and explicit missing checkpoint SHA status.

Archival source: Git commit `e02a753`, mounted at `archival/provenance/legacy_e02a753/`. It is ignored by the main release and is not mixed into canonical `results/`.

Checkpoint result:

- current tree: no checkpoint bytes;
- archival worktree: no checkpoint bytes;
- Git LFS: no tracked objects;
- CSV checkpoint paths are historical references only.

Therefore historical raw/derived evidence is partially recoverable, but frozen re-evaluation is blocked.

## Phase 2B — Endpoint schema

Frozen in [`docs/RECOVERY_ENDPOINT_PROTOCOL_V2.md`](RECOVERY_ENDPOINT_PROTOCOL_V2.md).

Primary strict endpoint:

```text
pre_failure_chain_established
AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

Primary duration:

```text
delta_t_loss_to_recovery = t_recovery - t_loss
```

The legacy onset-based first closure remains a secondary operational endpoint.

## Phase 2C — Statistical Gate B

The independent v2 implementation remains in `analysis/survival_v2/` and its synthetic tests pass. Historical v1.1 is not modified.

Third-party cross-validation could not be completed:

- `cac` lacks `lifelines`, `scikit-survival`, `statsmodels`, and R;
- isolated `cac_clean` also lacks the packages;
- installation from configured mirror and PyPI failed at SSL verification;
- SSL security was not weakened.

Gate B: **NO-GO**.

## Phase 2D — Paper–Code repair

Repaired the Method section to describe:

- shared node projection;
- edge features as scalar attention-score bias;
- role-pair message modulation;
- relation-specific layer instances;
- union/global residual branch;
- receiver/sender adjacency convention;
- No-Graph, Single-Graph, and canonical MAPPO distinction.

The repaired equivalence audit is [`docs/PAPER_CODE_EQUIVALENCE_AUDIT_V2.md`](PAPER_CODE_EQUIVALENCE_AUDIT_V2.md).

Gate A scientific semantics: **PARTIAL / NO-GO overall**, because the endpoint cannot yet be evaluated from complete raw fields and canonical baseline provenance is incomplete. Method formula equivalence itself: **PASS**.

## Phase 2E — Baseline identity/provenance

Created `archival/provenance/baseline_identity_manifest_v2.csv` with method family, graph encoder, config path/SHA, seed, checkpoint update, recorded checkpoint path, training/evaluation provenance, and explicit `MISSING_CHECKPOINT_BYTES` status.

No method identity is inferred from a filename. The historical `no_graph` rows are labeled `No-Graph (internal ablation)`; canonical MAPPO requires a separately bound run manifest.

Gate C evidence completeness: **NO-GO**.

## Reuse / re-evaluation / retraining

### Direct reuse for descriptive statistics

- terminal success/collision/timeout summaries;
- historical training logs and selection summaries as provenance diagnostics;
- legacy OOD/robustness results as provisional, non-canonical diagnostics.

### Requires frozen re-evaluation

- strict recovery endpoint and `t_loss`/`t_recovery` fields;
- canonical KM/RMST and hierarchical bootstrap;
- mechanism trajectories requiring checkpoint-level rollout traces;
- any result whose baseline identity or checkpoint mapping is unresolved.

### Requires retraining only if checkpoint recovery fails

- replacement of historical evaluation with new confirmatory results;
- any new union/global-residual ablation, Gate Prior sensitivity, random failure, scalability, or high-fidelity experiment.

New retraining must be labeled new confirmatory training and cannot be presented as reproduction of the historical package.

## Phase 2F — GO/NO-GO decision

| Gate | Status | Reason |
|---|---|---|
| Gate A: semantics/endpoint/paper-code | **NO-GO overall** | Method equations repaired, but strict endpoint fields and canonical baseline mapping remain incomplete |
| Gate B: survival/statistics | **NO-GO** | Standard third-party reference unavailable; empirical strict endpoint unavailable |
| Gate C: evidence/provenance | **NO-GO** | Checkpoint bytes and hashes missing; evidence packages have version/seed-count split |

## Final decision

**Phase 3 remains NO-GO.**

The project is GO for the next evidence-repair action: obtain checkpoint bytes and/or a standard survival environment, then perform frozen re-evaluation under Protocol v2. Until Gate A, B, and C all pass, do not start confirmatory training or update headline survival claims.
