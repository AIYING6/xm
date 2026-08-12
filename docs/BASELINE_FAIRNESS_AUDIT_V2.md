# Baseline Fairness Audit v2 (Phase 1)

Status: **PARTIAL PASS / evidence package incomplete**

## Intended definitions

- **No-Graph**: `graph_encoder=no_graph` within the same RI-GMAPPO implementation family, with graph aggregation disabled.
- **MAPPO**: canonical external no-graph CTDE baseline configured as `method=MAPPO`, also using `graph_encoder=no_graph`.
- **Single graph**: `graph_encoder=single`, an ordinary merged-adjacency graph-attention comparator.

The configuration files identify MAPPO as the standard CTDE no-graph baseline and No-Graph as an internal architecture ablation. This distinction is conceptually valid, but the current retained episode CSV labels all three graph variants with `method=EA-RG-MAPPO-S`; therefore the result file itself cannot prove the distinction without the originating run manifest.

## Fairness checks

| Dimension | Finding | Status |
|---|---|---|
| Environment | Same 3DOF environment and failure settings are represented in the retained Gate-1 CSV | Pass for retained CSV |
| Hidden width / role dimensions | Paper configs use hidden 64, role 8, intent 8 for EA, MAPPO, and single graph | Pass by config |
| BC initialization | All three paper configs specify `use_bc_initialization=true` | Pass by config |
| Training budget | Main Gate-1 config freezes a formal budget and validation-only checkpoint selection | Pass by protocol config; selected checkpoint bodies missing |
| Checkpoint selection | `checkpoint_selection_schema.yaml` requires validation selection, test once, and selection fields | Not auditable from current selected CSV alone |
| Method identity in raw CSV | Current merged episode CSV uses `method=EA-RG-MAPPO-S` for `no_graph`, `single`, and `multi_relation` | **Fail** |
| Strict endpoint fields in checkpoint selection schema | Schema expects pre-establishment and after-loss fields | Schema/data mismatch; **Fail** |
| Parameter matching | A separate parameter-matched single-graph config exists, but it is not part of the retained Gate-1 three-method CSV | Incomplete |

## Required correction

Before treating No-Graph as MAPPO in the manuscript, recover the run manifest/config/checkpoint mapping and generate a canonical baseline identity table. The paper must report No-Graph as an internal ablation and MAPPO as an independent baseline only when their training pipelines and labels are demonstrably distinct.

No training was started and no baseline protocol was changed in Phase 1.
