# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `single`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 53.8% | 88.0% | +34.2 pp | [+0.6, +71.8] pp |
| Post-failure chain recovered | 53.8% | 88.0% | +34.2 pp | [+0.6, +71.8] pp |
| Timeout | 44.4% | 12.0% | -32.4 pp | [-68.8, -0.4] pp |
| Restricted mean recovery steps | 101.39 | 37.60 | -63.78 | [-147.80, +5.71] |
| Tracking during failure | 47.1% | 76.0% | +29.0 pp | [-1.3, +62.1] pp |
| Connectivity during failure | 16.4% | 21.2% | +4.9 pp | [-1.0, +12.0] pp |
| Chain closure during failure | 8.1% | 12.9% | +4.8 pp | [-0.8, +11.4] pp |
| Episode length | 141.39 | 77.60 | -63.78 | [-147.80, +5.71] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| single | 269 | 5.94 |
| multi_relation | 440 | 12.73 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 72.0% | 57.0% | -15.0 pp |
| 0 | Post-failure chain recovered | 72.0% | 57.0% | -15.0 pp |
| 0 | Timeout | 28.0% | 43.0% | +15.0 pp |
| 0 | Restricted mean recovery steps | 65.90 | 97.75 | +31.85 |
| 0 | Tracking during failure | 76.2% | 63.3% | -13.0 pp |
| 0 | Connectivity during failure | 22.7% | 19.4% | -3.3 pp |
| 0 | Chain closure during failure | 11.1% | 9.1% | -2.0 pp |
| 0 | Episode length | 105.90 | 137.75 | +31.85 |
| 1 | Task success | 33.0% | 91.0% | +58.0 pp |
| 1 | Post-failure chain recovered | 33.0% | 91.0% | +58.0 pp |
| 1 | Timeout | 60.0% | 9.0% | -51.0 pp |
| 1 | Restricted mean recovery steps | 136.29 | 25.33 | -110.96 |
| 1 | Tracking during failure | 41.8% | 92.4% | +50.5 pp |
| 1 | Connectivity during failure | 13.5% | 21.8% | +8.3 pp |
| 1 | Chain closure during failure | 4.4% | 13.5% | +9.0 pp |
| 1 | Episode length | 176.29 | 65.33 | -110.96 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 98.0% | 0.0% | -98.0 pp |
| 2 | Restricted mean recovery steps | 216.01 | 5.37 | -210.64 |
| 2 | Tracking during failure | 12.4% | 100.0% | +87.6 pp |
| 2 | Connectivity during failure | 5.6% | 23.5% | +17.9 pp |
| 2 | Chain closure during failure | 0.0% | 16.2% | +16.2 pp |
| 2 | Episode length | 256.01 | 45.37 | -210.64 |
| 3 | Task success | 70.0% | 92.0% | +22.0 pp |
| 3 | Post-failure chain recovered | 70.0% | 92.0% | +22.0 pp |
| 3 | Timeout | 30.0% | 8.0% | -22.0 pp |
| 3 | Restricted mean recovery steps | 69.89 | 52.74 | -17.15 |
| 3 | Tracking during failure | 41.5% | 63.6% | +22.0 pp |
| 3 | Connectivity during failure | 17.4% | 18.3% | +0.9 pp |
| 3 | Chain closure during failure | 11.1% | 10.4% | -0.6 pp |
| 3 | Episode length | 109.89 | 92.74 | -17.15 |
| 4 | Task success | 94.0% | 100.0% | +6.0 pp |
| 4 | Post-failure chain recovered | 94.0% | 100.0% | +6.0 pp |
| 4 | Timeout | 6.0% | 0.0% | -6.0 pp |
| 4 | Restricted mean recovery steps | 18.84 | 6.83 | -12.01 |
| 4 | Tracking during failure | 63.4% | 61.0% | -2.4 pp |
| 4 | Connectivity during failure | 22.6% | 23.1% | +0.6 pp |
| 4 | Chain closure during failure | 14.2% | 15.4% | +1.2 pp |
| 4 | Episode length | 58.84 | 46.83 | -12.01 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
