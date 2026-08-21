# TC-SAM-D1 Sharpness Mechanism Analysis

The frozen offline probe used 24 actor-legal recorded F0 states per seed and a
0.01 relative actor-parameter perturbation. It used no rollout, optimizer step,
or environment mutation. Results are mechanism evidence only, not a decision
gate.

| Seed | UTR relay-deletion KL | TC-SAM relay-deletion KL | UTR parameter KL | TC-SAM parameter KL |
|---:|---:|---:|---:|---:|
| 2201 | 0.003494 | 0.019797 | 0.00001947 | 0.00000811 |
| 2202 | 0.014203 | 0.000760 | 0.00001913 | 0.00000719 |
| 2203 | 0.003269 | 0.000437 | 0.00001760 | 0.00001249 |
| 2204 | 0.000873 | 0.001422 | 0.00001957 | 0.00000769 |
| 2205 | 0.006204 | 0.001115 | 0.00001753 | 0.00000743 |

TC-SAM reduces parameter-perturbation sensitivity for all five seeds, but
relay-deletion sensitivity is mixed: it increases for seed2201 and seed2204
while decreasing for seed2202, seed2203, and seed2205. This does not establish
that lower local parameter sensitivity causes better topology robustness; it
also does not rescue the performance-level development FAIL.
