# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_role_pair_gate`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 64.8% | 88.6% | +23.8 pp | [+2.8, +59.2] pp |
| Post-failure chain recovered | 64.8% | 88.6% | +23.8 pp | [+2.8, +59.2] pp |
| Timeout | 35.2% | 11.4% | -23.8 pp | [-59.2, -2.8] pp |
| Restricted mean recovery steps | 87.74 | 36.02 | -51.72 | [-129.84, -5.77] |
| Tracking during failure | 60.7% | 77.6% | +16.9 pp | [+2.7, +38.8] pp |
| Connectivity during failure | 16.5% | 20.3% | +3.8 pp | [-0.3, +10.9] pp |
| Chain closure during failure | 9.9% | 13.8% | +3.9 pp | [+0.2, +10.2] pp |
| Episode length | 127.74 | 76.02 | -51.72 | [-129.84, -5.77] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_role_pair_gate | 324 | 15.90 |
| multi_relation | 443 | 12.35 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 53.0% | 65.0% | +12.0 pp |
| 0 | Post-failure chain recovered | 53.0% | 65.0% | +12.0 pp |
| 0 | Timeout | 47.0% | 35.0% | -12.0 pp |
| 0 | Restricted mean recovery steps | 106.11 | 80.40 | -25.71 |
| 0 | Tracking during failure | 59.8% | 70.4% | +10.6 pp |
| 0 | Connectivity during failure | 18.4% | 19.4% | +1.0 pp |
| 0 | Chain closure during failure | 8.8% | 10.7% | +1.9 pp |
| 0 | Episode length | 146.11 | 120.40 | -25.71 |
| 1 | Task success | 85.0% | 90.0% | +5.0 pp |
| 1 | Post-failure chain recovered | 85.0% | 90.0% | +5.0 pp |
| 1 | Timeout | 15.0% | 10.0% | -5.0 pp |
| 1 | Restricted mean recovery steps | 37.47 | 27.04 | -10.43 |
| 1 | Tracking during failure | 87.3% | 91.5% | +4.3 pp |
| 1 | Connectivity during failure | 21.3% | 21.2% | -0.0 pp |
| 1 | Chain closure during failure | 14.0% | 14.1% | +0.1 pp |
| 1 | Episode length | 77.47 | 67.04 | -10.43 |
| 2 | Task success | 100.0% | 99.0% | -1.0 pp |
| 2 | Post-failure chain recovered | 100.0% | 99.0% | -1.0 pp |
| 2 | Timeout | 0.0% | 1.0% | +1.0 pp |
| 2 | Restricted mean recovery steps | 5.03 | 7.16 | +2.13 |
| 2 | Tracking during failure | 100.0% | 99.2% | -0.8 pp |
| 2 | Connectivity during failure | 22.7% | 21.7% | -1.0 pp |
| 2 | Chain closure during failure | 17.1% | 16.8% | -0.3 pp |
| 2 | Episode length | 45.03 | 47.16 | +2.13 |
| 3 | Task success | 82.0% | 92.0% | +10.0 pp |
| 3 | Post-failure chain recovered | 82.0% | 92.0% | +10.0 pp |
| 3 | Timeout | 18.0% | 8.0% | -10.0 pp |
| 3 | Restricted mean recovery steps | 73.89 | 53.93 | -19.96 |
| 3 | Tracking during failure | 55.0% | 66.1% | +11.1 pp |
| 3 | Connectivity during failure | 16.2% | 17.4% | +1.2 pp |
| 3 | Chain closure during failure | 9.2% | 10.9% | +1.7 pp |
| 3 | Episode length | 113.89 | 93.93 | -19.96 |
| 4 | Task success | 4.0% | 97.0% | +93.0 pp |
| 4 | Post-failure chain recovered | 4.0% | 97.0% | +93.0 pp |
| 4 | Timeout | 96.0% | 3.0% | -93.0 pp |
| 4 | Restricted mean recovery steps | 216.20 | 11.58 | -204.62 |
| 4 | Tracking during failure | 1.6% | 60.9% | +59.3 pp |
| 4 | Connectivity during failure | 3.9% | 21.5% | +17.7 pp |
| 4 | Chain closure during failure | 0.1% | 16.2% | +16.1 pp |
| 4 | Episode length | 256.20 | 51.58 | -204.62 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
