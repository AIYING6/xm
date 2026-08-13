# Phase S2 Parameter-Matching Audit

Counts are computed from the current code without training:

| Method | Trainable parameters |
|---|---:|
| MAPPO | 35,771 |
| Parameter-Matched Single-Graph | 116,728 |
| Multi-Relation Full | 117,302 |

Single-Graph hidden width is 115. The absolute mismatch is 574 parameters,
or **0.4893%** relative to Full, within the frozen 5% tolerance. MAPPO is the
capacity-unmatched non-graph reference by definition.
