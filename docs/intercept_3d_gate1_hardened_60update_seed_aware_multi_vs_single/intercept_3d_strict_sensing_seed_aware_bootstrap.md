# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 150

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 61.3% | 85.3% | +24.0 pp | [-18.0, +76.7] pp |
| Post-failure chain recovered | 61.3% | 85.3% | +24.0 pp | [-18.0, +76.7] pp |
| Timeout | 37.3% | 14.0% | -23.3 pp | [-74.7, +18.0] pp |
| Restricted mean recovery steps | 86.03 | 36.13 | -49.89 | [-159.90, +38.89] |
| Tracking during failure | 66.9% | 87.0% | +20.0 pp | [-16.8, +65.7] pp |
| Connectivity during failure | 17.0% | 21.3% | +4.2 pp | [-2.0, +11.2] pp |
| Chain closure during failure | 9.0% | 12.5% | +3.5 pp | [-3.4, +11.1] pp |
| Episode length | 126.03 | 76.13 | -49.89 | [-159.90, +38.89] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 92 | 6.02 |
| multi_relation | 128 | 6.21 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 98.0% | 78.0% | -20.0 pp |
| 0 | Post-failure chain recovered | 98.0% | 78.0% | -20.0 pp |
| 0 | Timeout | 2.0% | 22.0% | +20.0 pp |
| 0 | Restricted mean recovery steps | 10.14 | 53.34 | +43.20 |
| 0 | Tracking during failure | 98.3% | 79.7% | -18.7 pp |
| 0 | Connectivity during failure | 22.2% | 19.9% | -2.3 pp |
| 0 | Chain closure during failure | 14.9% | 11.3% | -3.7 pp |
| 0 | Episode length | 50.14 | 93.34 | +43.20 |
| 1 | Task success | 8.0% | 86.0% | +78.0 pp |
| 1 | Post-failure chain recovered | 8.0% | 86.0% | +78.0 pp |
| 1 | Timeout | 88.0% | 12.0% | -76.0 pp |
| 1 | Restricted mean recovery steps | 194.76 | 31.90 | -162.86 |
| 1 | Tracking during failure | 21.2% | 88.2% | +66.9 pp |
| 1 | Connectivity during failure | 9.3% | 20.8% | +11.5 pp |
| 1 | Chain closure during failure | 1.0% | 12.4% | +11.4 pp |
| 1 | Episode length | 234.76 | 71.90 | -162.86 |
| 2 | Task success | 78.0% | 92.0% | +14.0 pp |
| 2 | Post-failure chain recovered | 78.0% | 92.0% | +14.0 pp |
| 2 | Timeout | 22.0% | 8.0% | -14.0 pp |
| 2 | Restricted mean recovery steps | 53.18 | 23.16 | -30.02 |
| 2 | Tracking during failure | 81.2% | 93.1% | +11.9 pp |
| 2 | Connectivity during failure | 19.5% | 23.1% | +3.6 pp |
| 2 | Chain closure during failure | 11.1% | 13.8% | +2.7 pp |
| 2 | Episode length | 93.18 | 63.16 | -30.02 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
