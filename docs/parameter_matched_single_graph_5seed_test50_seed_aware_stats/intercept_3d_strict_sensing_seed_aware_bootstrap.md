# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 250

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 33.2% | 89.2% | +56.0 pp | [+11.2, +98.8] pp |
| Post-failure chain recovered | 33.2% | 89.2% | +56.0 pp | [+11.2, +98.8] pp |
| Timeout | 66.8% | 10.8% | -56.0 pp | [-98.8, -11.2] pp |
| Restricted mean recovery steps | 154.09 | 33.17 | -120.92 | [-208.93, -29.97] |
| Tracking during failure | 20.3% | 78.9% | +58.6 pp | [+16.9, +91.7] pp |
| Connectivity during failure | 10.3% | 21.7% | +11.5 pp | [+3.9, +17.7] pp |
| Chain closure during failure | 4.0% | 13.4% | +9.4 pp | [+3.6, +15.0] pp |
| Episode length | 194.09 | 73.17 | -120.92 | [-208.93, -29.97] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 83 | 21.47 |
| multi_relation | 223 | 10.55 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 64.0% | 54.0% | -10.0 pp |
| 0 | Post-failure chain recovered | 64.0% | 54.0% | -10.0 pp |
| 0 | Timeout | 36.0% | 46.0% | +10.0 pp |
| 0 | Restricted mean recovery steps | 103.52 | 104.22 | +0.70 |
| 0 | Tracking during failure | 15.8% | 61.1% | +45.3 pp |
| 0 | Connectivity during failure | 12.7% | 19.4% | +6.7 pp |
| 0 | Chain closure during failure | 6.6% | 8.5% | +1.9 pp |
| 0 | Episode length | 143.52 | 144.22 | +0.70 |
| 1 | Task success | 0.0% | 98.0% | +98.0 pp |
| 1 | Post-failure chain recovered | 0.0% | 98.0% | +98.0 pp |
| 1 | Timeout | 100.0% | 2.0% | -98.0 pp |
| 1 | Restricted mean recovery steps | 220.00 | 10.32 | -209.68 |
| 1 | Tracking during failure | 0.5% | 98.3% | +97.8 pp |
| 1 | Connectivity during failure | 4.2% | 22.6% | +18.4 pp |
| 1 | Chain closure during failure | 0.0% | 14.5% | +14.5 pp |
| 1 | Episode length | 260.00 | 50.32 | -209.68 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.28 | -214.72 |
| 2 | Tracking during failure | 6.1% | 100.0% | +93.9 pp |
| 2 | Connectivity during failure | 7.0% | 23.0% | +16.1 pp |
| 2 | Chain closure during failure | 0.0% | 16.3% | +16.3 pp |
| 2 | Episode length | 260.00 | 45.28 | -214.72 |
| 3 | Task success | 2.0% | 98.0% | +96.0 pp |
| 3 | Post-failure chain recovered | 2.0% | 98.0% | +96.0 pp |
| 3 | Timeout | 98.0% | 2.0% | -96.0 pp |
| 3 | Restricted mean recovery steps | 219.96 | 25.98 | -193.98 |
| 3 | Tracking during failure | 1.8% | 78.4% | +76.7 pp |
| 3 | Connectivity during failure | 3.5% | 21.4% | +17.9 pp |
| 3 | Chain closure during failure | 0.0% | 13.0% | +13.0 pp |
| 3 | Episode length | 259.96 | 65.98 | -193.98 |
| 4 | Task success | 100.0% | 96.0% | -4.0 pp |
| 4 | Post-failure chain recovered | 100.0% | 96.0% | -4.0 pp |
| 4 | Timeout | 0.0% | 4.0% | +4.0 pp |
| 4 | Restricted mean recovery steps | 6.96 | 20.06 | +13.10 |
| 4 | Tracking during failure | 77.3% | 56.8% | -20.5 pp |
| 4 | Connectivity during failure | 23.9% | 22.1% | -1.8 pp |
| 4 | Chain closure during failure | 13.5% | 14.5% | +1.0 pp |
| 4 | Episode length | 46.96 | 60.06 | +13.10 |

## Interpretation

This five-seed test50 capacity-control candidate supports the conclusion that full multi-relation remains stronger than the parameter-matched single-graph baseline on average. The confidence intervals should still be reported with seed-level scatter because the single-graph baseline is competitive on seeds 0 and 4 but weak on seeds 1, 2, and 3.
