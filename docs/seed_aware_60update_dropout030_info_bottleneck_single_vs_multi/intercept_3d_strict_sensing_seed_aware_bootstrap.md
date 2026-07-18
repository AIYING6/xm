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
| Task success | 78.3% | 95.0% | +16.7 pp | [+3.3, +33.3] pp |
| Post-failure chain recovered | 78.3% | 95.0% | +16.7 pp | [+3.3, +33.3] pp |
| Timeout | 21.7% | 5.0% | -16.7 pp | [-33.3, -3.3] pp |
| Restricted mean recovery steps | 51.87 | 16.85 | -35.02 | [-69.82, -6.68] |
| Tracking during failure | 81.6% | 95.7% | +14.1 pp | [+2.8, +27.8] pp |
| Connectivity during failure | 31.1% | 31.6% | +0.5 pp | [-3.2, +3.5] pp |
| Chain closure during failure | 12.7% | 14.1% | +1.4 pp | [-0.3, +3.1] pp |
| Episode length | 91.87 | 56.85 | -35.02 | [-69.82, -6.68] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 47 | 5.36 |
| multi_relation | 57 | 6.16 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 70.0% | 100.0% | +30.0 pp |
| 0 | Post-failure chain recovered | 70.0% | 100.0% | +30.0 pp |
| 0 | Timeout | 30.0% | 0.0% | -30.0 pp |
| 0 | Restricted mean recovery steps | 69.70 | 6.70 | -63.00 |
| 0 | Tracking during failure | 74.6% | 99.9% | +25.3 pp |
| 0 | Connectivity during failure | 30.5% | 33.2% | +2.7 pp |
| 0 | Chain closure during failure | 11.4% | 13.9% | +2.4 pp |
| 0 | Episode length | 109.70 | 46.70 | -63.00 |
| 1 | Task success | 70.0% | 85.0% | +15.0 pp |
| 1 | Post-failure chain recovered | 70.0% | 85.0% | +15.0 pp |
| 1 | Timeout | 30.0% | 15.0% | -15.0 pp |
| 1 | Restricted mean recovery steps | 69.75 | 38.05 | -31.70 |
| 1 | Tracking during failure | 74.4% | 87.1% | +12.7 pp |
| 1 | Connectivity during failure | 29.8% | 31.5% | +1.8 pp |
| 1 | Chain closure during failure | 11.3% | 13.0% | +1.7 pp |
| 1 | Episode length | 109.75 | 78.05 | -31.70 |
| 2 | Task success | 95.0% | 100.0% | +5.0 pp |
| 2 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 2 | Timeout | 5.0% | 0.0% | -5.0 pp |
| 2 | Restricted mean recovery steps | 16.15 | 5.80 | -10.35 |
| 2 | Tracking during failure | 95.8% | 100.0% | +4.2 pp |
| 2 | Connectivity during failure | 33.1% | 30.2% | -2.9 pp |
| 2 | Chain closure during failure | 15.3% | 15.4% | +0.1 pp |
| 2 | Episode length | 56.15 | 45.80 | -10.35 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
