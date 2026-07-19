# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 150

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 26.7% | 85.3% | +58.7 pp | [+14.7, +90.7] pp |
| Post-failure chain recovered | 26.7% | 85.3% | +58.7 pp | [+14.7, +90.7] pp |
| Timeout | 73.3% | 14.0% | -59.3 pp | [-90.7, -16.7] pp |
| Restricted mean recovery steps | 162.81 | 36.13 | -126.68 | [-194.03, -34.99] |
| Tracking during failure | 16.1% | 87.0% | +70.9 pp | [+44.6, +92.0] pp |
| Connectivity during failure | 8.9% | 21.3% | +12.4 pp | [+3.5, +19.5] pp |
| Chain closure during failure | 4.2% | 12.5% | +8.3 pp | [+1.2, +13.6] pp |
| Episode length | 202.81 | 76.13 | -126.68 | [-194.03, -34.99] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 40 | 5.55 |
| multi_relation | 128 | 6.21 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 6.0% | 78.0% | +72.0 pp |
| 0 | Post-failure chain recovered | 6.0% | 78.0% | +72.0 pp |
| 0 | Timeout | 94.0% | 22.0% | -72.0 pp |
| 0 | Restricted mean recovery steps | 207.08 | 53.34 | -153.74 |
| 0 | Tracking during failure | 3.1% | 79.7% | +76.6 pp |
| 0 | Connectivity during failure | 5.4% | 19.9% | +14.5 pp |
| 0 | Chain closure during failure | 1.1% | 11.3% | +10.2 pp |
| 0 | Episode length | 247.08 | 93.34 | -153.74 |
| 1 | Task success | 74.0% | 86.0% | +12.0 pp |
| 1 | Post-failure chain recovered | 74.0% | 86.0% | +12.0 pp |
| 1 | Timeout | 26.0% | 12.0% | -14.0 pp |
| 1 | Restricted mean recovery steps | 61.36 | 31.90 | -29.46 |
| 1 | Tracking during failure | 45.1% | 88.2% | +43.1 pp |
| 1 | Connectivity during failure | 17.8% | 20.8% | +3.0 pp |
| 1 | Chain closure during failure | 11.5% | 12.4% | +0.8 pp |
| 1 | Episode length | 101.36 | 71.90 | -29.46 |
| 2 | Task success | 0.0% | 92.0% | +92.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 92.0% | +92.0 pp |
| 2 | Timeout | 100.0% | 8.0% | -92.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 23.16 | -196.84 |
| 2 | Tracking during failure | 0.0% | 93.1% | +93.1 pp |
| 2 | Connectivity during failure | 3.5% | 23.1% | +19.6 pp |
| 2 | Chain closure during failure | 0.0% | 13.8% | +13.8 pp |
| 2 | Episode length | 260.00 | 63.16 | -196.84 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
