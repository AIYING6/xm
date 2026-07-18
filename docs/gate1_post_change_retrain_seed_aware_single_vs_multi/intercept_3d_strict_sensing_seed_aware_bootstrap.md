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
| Task success | 35.0% | 95.0% | +60.0 pp | [+16.7, +90.0] pp |
| Post-failure chain recovered | 35.0% | 95.0% | +60.0 pp | [+16.7, +90.0] pp |
| Timeout | 63.3% | 5.0% | -58.3 pp | [-88.3, -16.7] pp |
| Restricted mean recovery steps | 141.73 | 16.13 | -125.60 | [-189.77, -34.88] |
| Tracking during failure | 44.7% | 95.6% | +50.9 pp | [+13.8, +76.1] pp |
| Connectivity during failure | 18.2% | 33.2% | +14.9 pp | [+2.8, +22.8] pp |
| Chain closure during failure | 5.9% | 15.4% | +9.5 pp | [+0.9, +15.2] pp |
| Episode length | 181.73 | 56.13 | -125.60 | [-189.77, -34.88] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 21 | 5.05 |
| multi_relation | 57 | 5.40 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 85.0% | 100.0% | +15.0 pp |
| 0 | Post-failure chain recovered | 85.0% | 100.0% | +15.0 pp |
| 0 | Timeout | 15.0% | 0.0% | -15.0 pp |
| 0 | Restricted mean recovery steps | 37.15 | 5.70 | -31.45 |
| 0 | Tracking during failure | 87.2% | 99.8% | +12.6 pp |
| 0 | Connectivity during failure | 31.4% | 34.0% | +2.6 pp |
| 0 | Chain closure during failure | 14.7% | 15.5% | +0.8 pp |
| 0 | Episode length | 77.15 | 45.70 | -31.45 |
| 1 | Task success | 5.0% | 85.0% | +80.0 pp |
| 1 | Post-failure chain recovered | 5.0% | 85.0% | +80.0 pp |
| 1 | Timeout | 90.0% | 15.0% | -75.0 pp |
| 1 | Restricted mean recovery steps | 200.15 | 37.60 | -162.55 |
| 1 | Tracking during failure | 20.2% | 87.1% | +66.9 pp |
| 1 | Connectivity during failure | 10.3% | 31.1% | +20.8 pp |
| 1 | Chain closure during failure | 0.8% | 13.6% | +12.8 pp |
| 1 | Episode length | 240.15 | 77.60 | -162.55 |
| 2 | Task success | 15.0% | 100.0% | +85.0 pp |
| 2 | Post-failure chain recovered | 15.0% | 100.0% | +85.0 pp |
| 2 | Timeout | 85.0% | 0.0% | -85.0 pp |
| 2 | Restricted mean recovery steps | 187.90 | 5.10 | -182.80 |
| 2 | Tracking during failure | 26.6% | 99.8% | +73.2 pp |
| 2 | Connectivity during failure | 13.0% | 34.4% | +21.4 pp |
| 2 | Chain closure during failure | 2.1% | 17.0% | +14.9 pp |
| 2 | Episode length | 227.90 | 45.10 | -182.80 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
