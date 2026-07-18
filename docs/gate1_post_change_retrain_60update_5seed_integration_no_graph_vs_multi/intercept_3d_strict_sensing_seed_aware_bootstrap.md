# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 50

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 26.0% | 94.0% | +68.0 pp | [+40.0, +94.0] pp |
| Post-failure chain recovered | 26.0% | 94.0% | +68.0 pp | [+40.0, +94.0] pp |
| Timeout | 74.0% | 6.0% | -68.0 pp | [-94.0, -40.0] pp |
| Restricted mean recovery steps | 164.24 | 27.32 | -136.92 | [-189.22, -81.56] |
| Tracking during failure | 18.6% | 81.7% | +63.1 pp | [+38.8, +86.2] pp |
| Connectivity during failure | 12.3% | 31.2% | +18.9 pp | [+11.6, +25.7] pp |
| Chain closure during failure | 4.1% | 14.4% | +10.3 pp | [+6.2, +14.4] pp |
| Episode length | 204.24 | 67.32 | -136.92 | [-189.22, -81.56] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 13 | 5.54 |
| multi_relation | 47 | 15.02 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 80.0% | +80.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 80.0% | +80.0 pp |
| 0 | Timeout | 100.0% | 20.0% | -80.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 48.30 | -171.70 |
| 0 | Tracking during failure | 6.8% | 83.3% | +76.4 pp |
| 0 | Connectivity during failure | 4.5% | 29.3% | +24.8 pp |
| 0 | Chain closure during failure | 0.0% | 13.0% | +13.0 pp |
| 0 | Episode length | 260.00 | 88.30 | -171.70 |
| 1 | Task success | 60.0% | 100.0% | +40.0 pp |
| 1 | Post-failure chain recovered | 60.0% | 100.0% | +40.0 pp |
| 1 | Timeout | 40.0% | 0.0% | -40.0 pp |
| 1 | Restricted mean recovery steps | 91.30 | 5.50 | -85.80 |
| 1 | Tracking during failure | 37.9% | 99.4% | +61.5 pp |
| 1 | Connectivity during failure | 22.0% | 33.2% | +11.2 pp |
| 1 | Chain closure during failure | 9.5% | 16.3% | +6.7 pp |
| 1 | Episode length | 131.30 | 45.50 | -85.80 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.20 | -214.80 |
| 2 | Tracking during failure | 0.5% | 100.0% | +99.5 pp |
| 2 | Connectivity during failure | 5.0% | 33.7% | +28.7 pp |
| 2 | Chain closure during failure | 0.0% | 16.6% | +16.6 pp |
| 2 | Episode length | 260.00 | 45.20 | -214.80 |
| 3 | Task success | 0.0% | 90.0% | +90.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 90.0% | +90.0 pp |
| 3 | Timeout | 100.0% | 10.0% | -90.0 pp |
| 3 | Restricted mean recovery steps | 220.00 | 72.50 | -147.50 |
| 3 | Tracking during failure | 0.0% | 59.0% | +59.0 pp |
| 3 | Connectivity during failure | 4.5% | 23.0% | +18.5 pp |
| 3 | Chain closure during failure | 0.0% | 9.4% | +9.4 pp |
| 3 | Episode length | 260.00 | 112.50 | -147.50 |
| 4 | Task success | 70.0% | 100.0% | +30.0 pp |
| 4 | Post-failure chain recovered | 70.0% | 100.0% | +30.0 pp |
| 4 | Timeout | 30.0% | 0.0% | -30.0 pp |
| 4 | Restricted mean recovery steps | 69.90 | 5.10 | -64.80 |
| 4 | Tracking during failure | 47.5% | 66.7% | +19.1 pp |
| 4 | Connectivity during failure | 25.4% | 36.7% | +11.4 pp |
| 4 | Chain closure during failure | 11.0% | 16.8% | +5.8 pp |
| 4 | Episode length | 109.90 | 45.10 | -64.80 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
