# Canonical parameter-count audit

| Method | Hidden width | Total | Actor | Critic | Gate | Union/global residual block |
|---|---:|---:|---:|---:|---:|---:|
| Final Full | 64 | 117,302 | 109,685 | 7,617 | 9,600 | 43,776 |
| MAPPO | 64 | 35,771 | 28,154 | 7,617 | 0 | 0 |
| Ordinary Single-Graph | 64 | 42,166 | 34,549 | 7,617 | 0 | 0 |
| Parameter-Matched Single-Graph | 115 | 116,728 | 97,177 | 19,551 | 0 | 0 |
| Full-no-union-residual | 64 | 117,302 | 109,685 | 7,617 | 9,600 | 43,776 |

The no-union model retains the same parameters but sets its union/global branch multiplier to zero; this is intentional isolation of branch contribution rather than capacity change.
