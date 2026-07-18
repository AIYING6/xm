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
| Task success | 96.7% | 98.3% | +1.7 pp | [-6.7, +10.0] pp |
| Post-failure chain recovered | 96.7% | 98.3% | +1.7 pp | [-6.7, +10.0] pp |
| Timeout | 3.3% | 1.7% | -1.7 pp | [-10.0, +6.7] pp |
| Restricted mean recovery steps | 12.55 | 9.57 | -2.98 | [-20.33, +14.57] |
| Tracking during failure | 97.0% | 98.6% | +1.5 pp | [-5.4, +8.5] pp |
| Connectivity during failure | 37.5% | 19.7% | -17.9 pp | [-24.0, -8.9] pp |
| Chain closure during failure | 15.8% | 15.0% | -0.8 pp | [-1.6, +0.2] pp |
| Episode length | 52.55 | 49.57 | -2.98 | [-20.33, +14.57] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 58 | 5.40 |
| multi_relation | 59 | 6.00 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 95.0% | 100.0% | +5.0 pp |
| 0 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 0 | Timeout | 5.0% | 0.0% | -5.0 pp |
| 0 | Restricted mean recovery steps | 15.80 | 5.60 | -10.20 |
| 0 | Tracking during failure | 95.4% | 99.8% | +4.5 pp |
| 0 | Connectivity during failure | 27.9% | 19.2% | -8.7 pp |
| 0 | Chain closure during failure | 16.3% | 16.3% | -0.0 pp |
| 0 | Episode length | 55.80 | 45.60 | -10.20 |
| 1 | Task success | 100.0% | 95.0% | -5.0 pp |
| 1 | Post-failure chain recovered | 100.0% | 95.0% | -5.0 pp |
| 1 | Timeout | 0.0% | 5.0% | +5.0 pp |
| 1 | Restricted mean recovery steps | 5.55 | 16.60 | +11.05 |
| 1 | Tracking during failure | 100.0% | 95.9% | -4.1 pp |
| 1 | Connectivity during failure | 41.5% | 19.9% | -21.5 pp |
| 1 | Chain closure during failure | 16.0% | 14.7% | -1.3 pp |
| 1 | Episode length | 45.55 | 56.60 | +11.05 |
| 2 | Task success | 95.0% | 100.0% | +5.0 pp |
| 2 | Post-failure chain recovered | 95.0% | 100.0% | +5.0 pp |
| 2 | Timeout | 5.0% | 0.0% | -5.0 pp |
| 2 | Restricted mean recovery steps | 16.30 | 6.50 | -9.80 |
| 2 | Tracking during failure | 95.7% | 100.0% | +4.3 pp |
| 2 | Connectivity during failure | 43.2% | 19.8% | -23.4 pp |
| 2 | Chain closure during failure | 15.1% | 14.1% | -1.0 pp |
| 2 | Episode length | 56.30 | 46.50 | -9.80 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
