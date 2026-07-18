# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 60

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 40.0% | 93.3% | +53.3 pp | [-3.3, +95.0] pp |
| Post-failure chain recovered | 40.0% | 93.3% | +53.3 pp | [-3.3, +95.0] pp |
| Timeout | 60.0% | 6.7% | -53.3 pp | [-95.0, +3.3] pp |
| Restricted mean recovery steps | 135.52 | 20.15 | -115.37 | [-202.62, +6.49] |
| Tracking during failure | 25.4% | 84.5% | +59.1 pp | [+24.6, +85.4] pp |
| Connectivity during failure | 20.9% | 42.8% | +21.9 pp | [+3.2, +34.7] pp |
| Chain closure during failure | 5.9% | 14.4% | +8.6 pp | [+0.3, +14.3] pp |
| Episode length | 175.52 | 60.15 | -115.37 | [-202.62, +6.49] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 24 | 8.79 |
| multi_relation | 56 | 5.88 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 25.0% | 100.0% | +75.0 pp |
| 0 | Post-failure chain recovered | 25.0% | 100.0% | +75.0 pp |
| 0 | Timeout | 75.0% | 0.0% | -75.0 pp |
| 0 | Restricted mean recovery steps | 169.70 | 5.50 | -164.20 |
| 0 | Tracking during failure | 18.9% | 90.2% | +71.3 pp |
| 0 | Connectivity during failure | 14.6% | 44.2% | +29.6 pp |
| 0 | Chain closure during failure | 3.6% | 16.3% | +12.8 pp |
| 0 | Episode length | 209.70 | 45.50 | -164.20 |
| 1 | Task success | 90.0% | 80.0% | -10.0 pp |
| 1 | Post-failure chain recovered | 90.0% | 80.0% | -10.0 pp |
| 1 | Timeout | 10.0% | 20.0% | +10.0 pp |
| 1 | Restricted mean recovery steps | 27.55 | 48.55 | +21.00 |
| 1 | Tracking during failure | 54.4% | 74.5% | +20.1 pp |
| 1 | Connectivity during failure | 39.6% | 41.3% | +1.7 pp |
| 1 | Chain closure during failure | 13.3% | 12.6% | -0.7 pp |
| 1 | Episode length | 67.55 | 88.55 | +21.00 |
| 2 | Task success | 5.0% | 100.0% | +95.0 pp |
| 2 | Post-failure chain recovered | 5.0% | 100.0% | +95.0 pp |
| 2 | Timeout | 95.0% | 0.0% | -95.0 pp |
| 2 | Restricted mean recovery steps | 209.30 | 6.40 | -202.90 |
| 2 | Tracking during failure | 2.8% | 88.8% | +86.0 pp |
| 2 | Connectivity during failure | 8.5% | 42.9% | +34.4 pp |
| 2 | Chain closure during failure | 0.7% | 14.3% | +13.6 pp |
| 2 | Episode length | 249.30 | 46.40 | -202.90 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
