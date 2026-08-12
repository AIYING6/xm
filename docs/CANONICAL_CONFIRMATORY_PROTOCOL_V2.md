# Canonical confirmatory protocol v2

**Status:** frozen protocol; no formal run was launched while creating this document.

This is a new confirmatory experiment protocol. It is not a rebranding or silent reproduction of historical 3-seed/10,800-episode results.

## Methods and identities

The first canonical comparison contains exactly these method identities:

| ID | Definition |
|---|---|
| `EA-RG-MAPPO-S` | Full EA-RG-MAPPO-S with shared node projection, relation-specific edge-score bias, role-pair message modulation, union/global residual branch, and staged topology/curriculum training |
| `MAPPO` | Canonical no-graph MAPPO baseline with the same task, failure process, reward, training budget, seed set, validation rule, and evaluation protocol |
| `Single-Graph` | Single-graph encoder ablation with all non-graph components held fixed |
| `EA-RG-MAPPO-S-no-union-residual` | Full method with only the union/global residual branch disabled; `multi_relation_global_residual_weight=0.0` |

Baseline identity is bound by the manifest, not by a filename or an ambiguous `method` column.

## Seeds, budget, and checkpoint selection

- Seeds: exactly `0, 1, 2, 3, 4` for the first canonical batch.
- The seed set and training budget are frozen before launch; no seed may be removed after observing results.
- Checkpoint selection is validation-only, using the pre-specified validation score and tie rule. Test episodes cannot select checkpoints.
- Every selected checkpoint is copied or content-addressed into `results/canonical_v2/checkpoints/` and recorded with SHA256, config SHA, seed, update, and code snapshot.

## Frozen task protocol

The current 3DOF intercept environment, observation interface, communication semantics, sender/receiver convention, message-age handling, sensing/dropout process, failure timing, target process, reward, horizon, and episode accounting are frozen from the audited implementation. Any change to these items requires a separate design document and commit before execution.

The first canonical evaluation uses the audited strict sensing/failure protocol: failure is applied at the pre-registered failure time and the relay/failure semantics are not adapted to improve an outcome. The evaluation horizon, episode count per scenario, scenario definitions, and randomization stream are recorded in the run manifest before execution.

## Endpoint and survival analysis

The primary endpoint is the strict cohort in [`RECOVERY_ENDPOINT_PROTOCOL_V2.md`](RECOVERY_ENDPOINT_PROTOCOL_V2.md):

```text
pre_failure_chain_established AND chain_lost_after_failure
AND post_failure_chain_recovered_after_loss
```

Primary duration is `delta_t_loss_to_recovery = t_recovery - t_loss`. The secondary endpoint is onset-to-first post-failure establishment. Both endpoints and the censor cohort are written to raw episode CSV before derived statistics.

- Primary tau: `80` time units.
- Sensitivity taus: `50, 80, 100, 150, 190, 220`.
- KM and RMST are computed with the independent v2 implementation and a standard reference implementation.
- Hierarchical bootstrap: `10,000` replicates, resampling seeds first and episode IDs within seed/scenario second; paired episode IDs are retained for method contrasts.
- Confidence intervals: two-sided 95% percentile intervals, with the bootstrap seed and software versions recorded.
- Each tau has its own observed delta and provenance row.

## Canonical evidence contract

No result is headline-eligible unless the method/seed has: frozen config and SHA, code snapshot, selected checkpoint and SHA, validation selection record, raw episode CSV with the frozen schema, manifest, derived survival table, KM/RMST reference comparison, bootstrap provenance, and generated table/figure hashes.

## Launch gate

Formal training remains **NO-GO** until Gate A1 (scientific protocol), Gate B1 (standard survival validation), Gate H (historical disposition), and Gate C0 (canonical evidence contract) are all PASS. This protocol alone does not authorize training.
