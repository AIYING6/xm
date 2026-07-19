# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 5
- Matched test episodes: 500

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 23.2% | 88.2% | +65.0 pp | [+27.2, +93.2] pp |
| Post-failure chain recovered | 23.2% | 88.2% | +65.0 pp | [+27.2, +93.2] pp |
| Timeout | 75.6% | 11.6% | -64.0 pp | [-91.0, -27.2] pp |
| Restricted mean recovery steps | 183.93 | 50.28 | -133.65 | [-189.07, -57.10] |
| Tracking during failure | 18.0% | 65.9% | +47.9 pp | [+31.4, +62.8] pp |
| Connectivity during failure | 11.9% | 21.9% | +10.0 pp | [+4.4, +13.7] pp |
| Chain closure during failure | 1.1% | 3.9% | +2.8 pp | [+1.1, +4.1] pp |
| Episode length | 208.93 | 75.28 | -133.65 | [-189.07, -57.10] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 116 | 22.16 |
| multi_relation | 441 | 26.04 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 1.0% | 57.0% | +56.0 pp |
| 0 | Post-failure chain recovered | 1.0% | 57.0% | +56.0 pp |
| 0 | Timeout | 99.0% | 43.0% | -56.0 pp |
| 0 | Restricted mean recovery steps | 234.85 | 112.73 | -122.12 |
| 0 | Tracking during failure | 8.3% | 57.4% | +49.1 pp |
| 0 | Connectivity during failure | 8.3% | 19.6% | +11.3 pp |
| 0 | Chain closure during failure | 0.0% | 2.7% | +2.7 pp |
| 0 | Episode length | 259.85 | 137.73 | -122.12 |
| 1 | Task success | 97.0% | 91.0% | -6.0 pp |
| 1 | Post-failure chain recovered | 97.0% | 91.0% | -6.0 pp |
| 1 | Timeout | 3.0% | 8.0% | +5.0 pp |
| 1 | Restricted mean recovery steps | 27.06 | 38.23 | +11.17 |
| 1 | Tracking during failure | 56.3% | 75.7% | +19.4 pp |
| 1 | Connectivity during failure | 23.4% | 22.7% | -0.7 pp |
| 1 | Chain closure during failure | 4.5% | 4.1% | -0.4 pp |
| 1 | Episode length | 52.06 | 63.23 | +11.17 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 94.0% | 0.0% | -94.0 pp |
| 2 | Restricted mean recovery steps | 226.54 | 20.36 | -206.18 |
| 2 | Tracking during failure | 7.1% | 79.7% | +72.5 pp |
| 2 | Connectivity during failure | 8.3% | 23.4% | +15.1 pp |
| 2 | Chain closure during failure | 0.0% | 4.7% | +4.7 pp |
| 2 | Episode length | 251.54 | 45.36 | -206.18 |
| 3 | Task success | 0.0% | 93.0% | +93.0 pp |
| 3 | Post-failure chain recovered | 0.0% | 93.0% | +93.0 pp |
| 3 | Timeout | 100.0% | 7.0% | -93.0 pp |
| 3 | Restricted mean recovery steps | 235.00 | 59.45 | -175.55 |
| 3 | Tracking during failure | 3.2% | 54.6% | +51.5 pp |
| 3 | Connectivity during failure | 7.9% | 20.4% | +12.5 pp |
| 3 | Chain closure during failure | 0.0% | 3.4% | +3.4 pp |
| 3 | Episode length | 260.00 | 84.45 | -175.55 |
| 4 | Task success | 18.0% | 100.0% | +82.0 pp |
| 4 | Post-failure chain recovered | 18.0% | 100.0% | +82.0 pp |
| 4 | Timeout | 82.0% | 0.0% | -82.0 pp |
| 4 | Restricted mean recovery steps | 196.20 | 20.61 | -175.59 |
| 4 | Tracking during failure | 15.3% | 62.3% | +47.0 pp |
| 4 | Connectivity during failure | 11.6% | 23.4% | +11.8 pp |
| 4 | Chain closure during failure | 0.9% | 4.6% | +3.8 pp |
| 4 | Episode length | 221.20 | 45.61 | -175.59 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
