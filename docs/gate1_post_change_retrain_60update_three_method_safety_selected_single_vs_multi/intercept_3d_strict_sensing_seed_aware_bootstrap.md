# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 60

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 38.3% | 98.3% | +60.0 pp | [+26.7, +86.7] pp |
| Post-failure chain recovered | 38.3% | 98.3% | +60.0 pp | [+26.7, +86.7] pp |
| Timeout | 61.7% | 1.7% | -60.0 pp | [-86.7, -26.7] pp |
| Restricted mean recovery steps | 138.00 | 9.32 | -128.68 | [-186.23, -57.12] |
| Tracking during failure | 47.2% | 98.6% | +51.4 pp | [+22.9, +74.8] pp |
| Connectivity during failure | 19.7% | 33.1% | +13.4 pp | [+3.3, +20.9] pp |
| Chain closure during failure | 5.6% | 15.2% | +9.6 pp | [+4.0, +14.4] pp |
| Episode length | 178.00 | 49.32 | -128.68 | [-186.23, -57.12] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 23 | 6.09 |
| multi_relation | 59 | 5.75 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 75.0% | 100.0% | +25.0 pp |
| 0 | Post-failure chain recovered | 75.0% | 100.0% | +25.0 pp |
| 0 | Timeout | 25.0% | 0.0% | -25.0 pp |
| 0 | Restricted mean recovery steps | 59.35 | 5.90 | -53.45 |
| 0 | Tracking during failure | 78.6% | 100.0% | +21.4 pp |
| 0 | Connectivity during failure | 31.0% | 34.0% | +3.1 pp |
| 0 | Chain closure during failure | 11.5% | 15.2% | +3.7 pp |
| 0 | Episode length | 99.35 | 45.90 | -53.45 |
| 1 | Task success | 25.0% | 95.0% | +70.0 pp |
| 1 | Post-failure chain recovered | 25.0% | 95.0% | +70.0 pp |
| 1 | Timeout | 75.0% | 5.0% | -70.0 pp |
| 1 | Restricted mean recovery steps | 166.65 | 16.65 | -150.00 |
| 1 | Tracking during failure | 36.3% | 95.7% | +59.4 pp |
| 1 | Connectivity during failure | 14.8% | 32.4% | +17.7 pp |
| 1 | Chain closure during failure | 3.3% | 14.4% | +11.0 pp |
| 1 | Episode length | 206.65 | 56.65 | -150.00 |
| 2 | Task success | 15.0% | 100.0% | +85.0 pp |
| 2 | Post-failure chain recovered | 15.0% | 100.0% | +85.0 pp |
| 2 | Timeout | 85.0% | 0.0% | -85.0 pp |
| 2 | Restricted mean recovery steps | 188.00 | 5.40 | -182.60 |
| 2 | Tracking during failure | 26.6% | 100.0% | +73.4 pp |
| 2 | Connectivity during failure | 13.4% | 33.0% | +19.6 pp |
| 2 | Chain closure during failure | 2.0% | 16.1% | +14.1 pp |
| 2 | Episode length | 228.00 | 45.40 | -182.60 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
