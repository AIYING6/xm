# Paper–Code Equivalence Audit v2

Status: **PASS for the repaired Method section; numerical claims intentionally not audited here**

Compared at frozen code baseline `4122f6d` against the repaired `paper_latex_3d_en/sections/04_method.tex`.

| Item | Code fact | Repaired paper description | Status |
|---|---|---|---|
| Adjacency orientation | `A[receiver, sender]` in environment graph construction | Explicit receiver/sender convention | PASS |
| Node projection | One `self.proj` per attention layer | Shared projection `W h_i`, `W h_j` | PASS |
| Edge features | `edge_score(edge_feat)` adds scalar score bias | Edge feature enters attention score through `b(e_ij)` | PASS |
| Message payload | Projected sender `h'_j` multiplied by attention and role gate | `m=A alpha mu h'_j`; no payload concatenation claim | PASS |
| Relation parameterization | Separate layer instances in each relation channel | Independent role-conditioned relation layers | PASS |
| Role-pair modulation | `sigmoid(role_pair_gate[receiver_role,sender_role])` multiplies sender message | Static receiver–sender role-pair modulation | PASS |
| Union/global path | Separate global layers over union adjacency, fused with relation outputs | Explicit union/global residual information path | PASS |
| No-Graph | `graph_encoder=no_graph` in RI-MAPPO actor pipeline | Internal No-Graph ablation | PASS |
| Single graph | `graph_encoder=single` with merged adjacency | Ordinary merged-adjacency graph comparator | PASS |
| Canonical MAPPO | Separate config identity required; not inferred from raw CSV | Paper text now distinguishes canonical MAPPO from internal No-Graph | PASS with provenance blocker |

## Boundary

This PASS concerns implementation description only. It does not certify the historical result package, checkpoint provenance, survival statistics, or the consistency of all experiment-section numbers.
