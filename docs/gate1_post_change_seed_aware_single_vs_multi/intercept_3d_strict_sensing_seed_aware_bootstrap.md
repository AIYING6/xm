# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 30

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 26.7% | 86.7% | +60.0 pp | [+20.0, +93.3] pp |
| Post-failure chain recovered | 26.7% | 86.7% | +60.0 pp | [+20.0, +93.3] pp |
| Timeout | 70.0% | 13.3% | -56.7 pp | [-86.7, -20.0] pp |
| Restricted mean recovery steps | 155.97 | 34.57 | -121.40 | [-186.63, -42.03] |
| Tracking during failure | 39.4% | 88.6% | +49.2 pp | [+16.8, +76.2] pp |
| Connectivity during failure | 17.9% | 32.7% | +14.8 pp | [+3.7, +23.6] pp |
| Chain closure during failure | 4.2% | 13.2% | +9.0 pp | [+1.7, +15.2] pp |
| Episode length | 195.97 | 74.57 | -121.40 | [-186.63, -42.03] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 8 | 5.62 |
| multi_relation | 26 | 6.04 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 60.0% | 80.0% | +20.0 pp |
| 0 | Post-failure chain recovered | 60.0% | 80.0% | +20.0 pp |
| 0 | Timeout | 40.0% | 20.0% | -20.0 pp |
| 0 | Restricted mean recovery steps | 91.00 | 48.80 | -42.20 |
| 0 | Tracking during failure | 65.9% | 83.5% | +17.7 pp |
| 0 | Connectivity during failure | 28.3% | 31.8% | +3.5 pp |
| 0 | Chain closure during failure | 10.3% | 12.2% | +1.8 pp |
| 0 | Episode length | 131.00 | 88.80 | -42.20 |
| 1 | Task success | 10.0% | 80.0% | +70.0 pp |
| 1 | Post-failure chain recovered | 10.0% | 80.0% | +70.0 pp |
| 1 | Timeout | 90.0% | 20.0% | -70.0 pp |
| 1 | Restricted mean recovery steps | 198.80 | 49.20 | -149.60 |
| 1 | Tracking during failure | 23.9% | 82.1% | +58.2 pp |
| 1 | Connectivity during failure | 10.8% | 29.7% | +18.9 pp |
| 1 | Chain closure during failure | 1.1% | 11.5% | +10.4 pp |
| 1 | Episode length | 238.80 | 89.20 | -149.60 |
| 2 | Task success | 10.0% | 100.0% | +90.0 pp |
| 2 | Post-failure chain recovered | 10.0% | 100.0% | +90.0 pp |
| 2 | Timeout | 80.0% | 0.0% | -80.0 pp |
| 2 | Restricted mean recovery steps | 178.10 | 5.70 | -172.40 |
| 2 | Tracking during failure | 28.3% | 100.0% | +71.7 pp |
| 2 | Connectivity during failure | 14.5% | 36.6% | +22.0 pp |
| 2 | Chain closure during failure | 1.2% | 16.0% | +14.7 pp |
| 2 | Episode length | 218.10 | 45.70 | -172.40 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
