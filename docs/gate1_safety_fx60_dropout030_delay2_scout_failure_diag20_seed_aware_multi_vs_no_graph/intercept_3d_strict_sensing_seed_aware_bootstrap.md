# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing evaluation episodes from the selected scenario.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 100

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 37.0% | 85.0% | +48.0 pp | [+4.0, +86.0] pp |
| Post-failure chain recovered | 37.0% | 85.0% | +48.0 pp | [+4.0, +86.0] pp |
| Timeout | 63.0% | 15.0% | -48.0 pp | [-86.0, -4.0] pp |
| Restricted mean recovery steps | 142.27 | 37.69 | -104.58 | [-188.37, -8.43] |
| Tracking during failure | 23.8% | 78.3% | +54.5 pp | [+22.6, +84.7] pp |
| Connectivity during failure | 17.5% | 21.8% | +4.3 pp | [-1.2, +10.1] pp |
| Chain closure during failure | 5.9% | 13.6% | +7.7 pp | [+0.2, +14.3] pp |
| Episode length | 182.27 | 77.69 | -104.58 | [-188.37, -8.43] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 37 | 9.92 |
| multi_relation | 85 | 5.52 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 5.0% | 80.0% | +75.0 pp |
| 0 | Post-failure chain recovered | 5.0% | 80.0% | +75.0 pp |
| 0 | Timeout | 95.0% | 20.0% | -75.0 pp |
| 0 | Restricted mean recovery steps | 217.80 | 48.70 | -169.10 |
| 0 | Tracking during failure | 6.0% | 82.9% | +76.9 pp |
| 0 | Connectivity during failure | 8.9% | 23.4% | +14.4 pp |
| 0 | Chain closure during failure | 0.0% | 12.4% | +12.4 pp |
| 0 | Episode length | 257.80 | 88.70 | -169.10 |
| 1 | Task success | 100.0% | 70.0% | -30.0 pp |
| 1 | Post-failure chain recovered | 100.0% | 70.0% | -30.0 pp |
| 1 | Timeout | 0.0% | 30.0% | +30.0 pp |
| 1 | Restricted mean recovery steps | 5.60 | 70.10 | +64.50 |
| 1 | Tracking during failure | 66.2% | 74.5% | +8.3 pp |
| 1 | Connectivity during failure | 22.8% | 19.4% | -3.4 pp |
| 1 | Chain closure during failure | 15.9% | 10.6% | -5.3 pp |
| 1 | Episode length | 45.60 | 110.10 | +64.50 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.15 | -214.85 |
| 2 | Tracking during failure | 0.4% | 100.0% | +99.6 pp |
| 2 | Connectivity during failure | 22.1% | 22.2% | +0.1 pp |
| 2 | Chain closure during failure | 0.0% | 16.7% | +16.7 pp |
| 2 | Episode length | 260.00 | 45.15 | -214.85 |
| 3 | Task success | 0.0% | 75.0% | +75.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 75.0% | +75.0 pp |
| 3 | Timeout | 100.0% | 25.0% | -75.0 pp |
| 3 | Restricted mean recovery steps | 220.00 | 59.00 | -161.00 |
| 3 | Tracking during failure | 0.0% | 68.7% | +68.7 pp |
| 3 | Connectivity during failure | 13.7% | 21.8% | +8.1 pp |
| 3 | Chain closure during failure | 0.0% | 12.3% | +12.3 pp |
| 3 | Episode length | 260.00 | 99.00 | -161.00 |
| 4 | Task success | 80.0% | 100.0% | +20.0 pp |
| 4 | Post-failure chain recovered | 80.0% | 100.0% | +20.0 pp |
| 4 | Timeout | 20.0% | 0.0% | -20.0 pp |
| 4 | Restricted mean recovery steps | 47.95 | 5.50 | -42.45 |
| 4 | Tracking during failure | 46.5% | 65.5% | +19.0 pp |
| 4 | Connectivity during failure | 19.8% | 22.0% | +2.2 pp |
| 4 | Chain closure during failure | 13.7% | 16.1% | +2.3 pp |
| 4 | Episode length | 87.95 | 45.50 | -42.45 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
