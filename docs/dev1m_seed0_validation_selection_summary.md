# Seed-0 Validation Checkpoint Selection Summary

Generated: 2026-07-26

Protocol: strict-sensing relay-failure validation split, 50 matched episodes per checkpoint, zero-collision selection gate.

| Method | Selected update | Success | Recovery | Recovery steps | Collision | Selection score |
|---|---:|---:|---:|---:|---:|---:|
| EA-RG-MAPPO | 1600 | 0.94 | 0.94 | 19.7447 | 0 | 1014.26 |
| Single-Graph MAPPO | 3907 | 0.82 | 0.82 | 19.2927 | 0 | 882.707 |
| MAPPO/no-graph | 3800 | 0.62 | 0.62 | 17.8065 | 0 | 664.194 |
| HAPPO | 900 | 0.14 | 0.14 | 81.2857 | 0 | 72.7143 |

Interpretation: seed-0 validation shows a monotonic ordering from no graph to single graph to multi-relation role graph, while standard HAPPO remains weak under the strict sensing and relay-failure setting. These are checkpoint-selection results only; final claims require frozen test-split evaluation and multi-seed confirmation.
