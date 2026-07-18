# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 30

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 30.0% | 86.7% | +56.7 pp | [-6.7, +100.0] pp |
| Post-failure chain recovered | 30.0% | 86.7% | +56.7 pp | [-6.7, +100.0] pp |
| Timeout | 70.0% | 13.3% | -56.7 pp | [-100.0, +6.7] pp |
| Restricted mean recovery steps | 155.73 | 34.57 | -121.17 | [-214.30, +14.60] |
| Tracking during failure | 18.6% | 88.6% | +69.9 pp | [+30.0, +99.7] pp |
| Connectivity during failure | 12.9% | 32.7% | +19.8 pp | [+2.2, +32.1] pp |
| Chain closure during failure | 4.7% | 13.2% | +8.5 pp | [-1.7, +16.1] pp |
| Episode length | 195.73 | 74.57 | -121.17 | [-214.30, +14.60] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 9 | 5.78 |
| multi_relation | 26 | 6.04 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 80.0% | +80.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 80.0% | +80.0 pp |
| 0 | Timeout | 100.0% | 20.0% | -80.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 48.80 | -171.20 |
| 0 | Tracking during failure | 0.0% | 83.5% | +83.5 pp |
| 0 | Connectivity during failure | 4.7% | 31.8% | +27.2 pp |
| 0 | Chain closure during failure | 0.0% | 12.2% | +12.2 pp |
| 0 | Episode length | 260.00 | 88.80 | -171.20 |
| 1 | Task success | 90.0% | 80.0% | -10.0 pp |
| 1 | Post-failure chain recovered | 90.0% | 80.0% | -10.0 pp |
| 1 | Timeout | 10.0% | 20.0% | +10.0 pp |
| 1 | Restricted mean recovery steps | 27.20 | 49.20 | +22.00 |
| 1 | Tracking during failure | 55.5% | 82.1% | +26.6 pp |
| 1 | Connectivity during failure | 29.4% | 29.7% | +0.3 pp |
| 1 | Chain closure during failure | 14.1% | 11.5% | -2.6 pp |
| 1 | Episode length | 67.20 | 89.20 | +22.00 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.70 | -214.30 |
| 2 | Tracking during failure | 0.4% | 100.0% | +99.6 pp |
| 2 | Connectivity during failure | 4.5% | 36.6% | +32.0 pp |
| 2 | Chain closure during failure | 0.0% | 16.0% | +16.0 pp |
| 2 | Episode length | 260.00 | 45.70 | -214.30 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
