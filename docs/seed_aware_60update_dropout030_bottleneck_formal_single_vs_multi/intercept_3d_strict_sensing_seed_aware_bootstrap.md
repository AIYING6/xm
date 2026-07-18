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
| Task success | 78.3% | 95.0% | +16.7 pp | [+6.7, +28.3] pp |
| Post-failure chain recovered | 78.3% | 95.0% | +16.7 pp | [+6.7, +28.3] pp |
| Timeout | 21.7% | 5.0% | -16.7 pp | [-28.3, -6.7] pp |
| Restricted mean recovery steps | 51.73 | 16.48 | -35.25 | [-60.12, -13.60] |
| Tracking during failure | 81.8% | 95.8% | +14.0 pp | [+5.5, +23.9] pp |
| Connectivity during failure | 30.2% | 31.9% | +1.7 pp | [-0.5, +3.9] pp |
| Chain closure during failure | 13.0% | 14.7% | +1.7 pp | [+0.1, +3.6] pp |
| Episode length | 91.73 | 56.48 | -35.25 | [-60.12, -13.60] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 47 | 5.19 |
| multi_relation | 57 | 5.77 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 75.0% | 95.0% | +20.0 pp |
| 0 | Post-failure chain recovered | 75.0% | 95.0% | +20.0 pp |
| 0 | Timeout | 25.0% | 5.0% | -20.0 pp |
| 0 | Restricted mean recovery steps | 58.90 | 17.05 | -41.85 |
| 0 | Tracking during failure | 78.9% | 95.8% | +16.9 pp |
| 0 | Connectivity during failure | 31.2% | 32.8% | +1.6 pp |
| 0 | Chain closure during failure | 12.4% | 13.7% | +1.2 pp |
| 0 | Episode length | 98.90 | 57.05 | -41.85 |
| 1 | Task success | 70.0% | 90.0% | +20.0 pp |
| 1 | Post-failure chain recovered | 70.0% | 90.0% | +20.0 pp |
| 1 | Timeout | 30.0% | 10.0% | -20.0 pp |
| 1 | Restricted mean recovery steps | 69.55 | 26.95 | -42.60 |
| 1 | Tracking during failure | 74.7% | 91.5% | +16.9 pp |
| 1 | Connectivity during failure | 29.1% | 30.8% | +1.8 pp |
| 1 | Chain closure during failure | 11.9% | 14.4% | +2.5 pp |
| 1 | Episode length | 109.55 | 66.95 | -42.60 |
| 2 | Task success | 90.0% | 100.0% | +10.0 pp |
| 2 | Post-failure chain recovered | 90.0% | 100.0% | +10.0 pp |
| 2 | Timeout | 10.0% | 0.0% | -10.0 pp |
| 2 | Restricted mean recovery steps | 26.75 | 5.45 | -21.30 |
| 2 | Tracking during failure | 91.7% | 100.0% | +8.3 pp |
| 2 | Connectivity during failure | 30.3% | 32.0% | +1.6 pp |
| 2 | Chain closure during failure | 14.7% | 16.0% | +1.4 pp |
| 2 | Episode length | 66.75 | 45.45 | -21.30 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
