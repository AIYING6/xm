# Final 300-Episode Paired Statistics

Purpose:

```text
Provide a seed-paired descriptive confidence-interval check for the final 300-episode main results.
The sample size is three seeds, so these intervals are evidence-strength diagnostics rather than a stand-alone significance claim.
Positive success_gain means EA-RG-MAPPO-S has higher success than the baseline.
Positive collision_reduction means EA-RG-MAPPO-S has lower collision than the baseline.
```

## Paired Differences

| Baseline | Radius | Success gain, mean [95% CI] | Collision reduction, mean [95% CI] |
|---|---:|---:|---:|
| MAPPO | 4 | 0.219 [-0.279, 0.716] | 0.173 [-0.107, 0.454] |
| MAPPO | 6 | 0.149 [-0.287, 0.585] | 0.153 [-0.247, 0.554] |
| MAPPO | 8 | 0.080 [-0.293, 0.453] | 0.093 [-0.253, 0.440] |
| MAPPO | 10 | 0.043 [-0.172, 0.259] | 0.067 [-0.154, 0.287] |
| GAT-MAPPO | 4 | 0.114 [0.036, 0.193] | 0.081 [0.039, 0.123] |
| GAT-MAPPO | 6 | 0.081 [-0.048, 0.210] | 0.061 [-0.044, 0.166] |
| GAT-MAPPO | 8 | 0.106 [0.005, 0.206] | 0.096 [0.005, 0.186] |
| GAT-MAPPO | 10 | 0.077 [-0.068, 0.222] | 0.070 [-0.028, 0.168] |

## Use in Paper

```text
Use as supplementary support for robustness and collision-reduction claims.
Do not phrase this as definitive statistical significance because n=3 makes the confidence intervals intentionally conservative.
```
