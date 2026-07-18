# Strict-Sensing Seed-Aware Statistics

This report uses matched strict-sensing relay-failure test episodes from the formal development runs.
Uncertainty is estimated with a hierarchical bootstrap: training seeds are resampled first, then matched episodes are resampled within each selected training seed.

- Baseline: `no_graph`
- Proposed: `multi_relation`
- Independent training seeds: 3
- Matched test episodes: 60

## Bootstrap Summary

| Metric | Baseline | Proposed | Delta | 95% CI for delta |
|---|---:|---:|---:|---:|
| Task success | 31.7% | 98.3% | +66.7 pp | [+1.7, +100.0] pp |
| Post-failure chain recovered | 31.7% | 98.3% | +66.7 pp | [+1.7, +100.0] pp |
| Timeout | 68.3% | 1.7% | -66.7 pp | [-100.0, -1.7] pp |
| Restricted mean recovery steps | 152.05 | 9.32 | -142.73 | [-214.65, -3.28] |
| Tracking during failure | 20.4% | 98.6% | +78.2 pp | [+37.1, +100.0] pp |
| Connectivity during failure | 14.4% | 33.1% | +18.7 pp | [-0.5, +29.8] pp |
| Chain closure during failure | 5.1% | 15.2% | +10.1 pp | [-0.4, +16.3] pp |
| Episode length | 192.05 | 49.32 | -142.73 | [-214.65, -3.28] |

## Recovery-Time Handling

Recovery probability and recovery time are reported separately. For the comparable recovery-time proxy, unrecovered episodes are assigned the remaining horizon after relay failure (`max_steps - node_failure_start_step`), producing a restricted mean recovery time. Conditional recovered-only means are listed below only as descriptive diagnostics.

| Method | Recovered episodes | Recovered-only mean steps |
|---|---:|---:|
| no_graph | 19 | 5.42 |
| multi_relation | 59 | 5.75 |

## Seed-Level Deltas

| Seed | Metric | Baseline | Proposed | Delta |
|---:|---|---:|---:|---:|
| 0 | Task success | 0.0% | 100.0% | +100.0 pp |
| 0 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 0 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 0 | Restricted mean recovery steps | 220.00 | 5.90 | -214.10 |
| 0 | Tracking during failure | 0.0% | 100.0% | +100.0 pp |
| 0 | Connectivity during failure | 4.7% | 34.0% | +29.4 pp |
| 0 | Chain closure during failure | 0.0% | 15.2% | +15.2 pp |
| 0 | Episode length | 260.00 | 45.90 | -214.10 |
| 1 | Task success | 95.0% | 95.0% | +0.0 pp |
| 1 | Post-failure chain recovered | 95.0% | 95.0% | +0.0 pp |
| 1 | Timeout | 5.0% | 5.0% | +0.0 pp |
| 1 | Restricted mean recovery steps | 16.15 | 16.65 | +0.50 |
| 1 | Tracking during failure | 60.3% | 95.7% | +35.4 pp |
| 1 | Connectivity during failure | 33.8% | 32.4% | -1.3 pp |
| 1 | Chain closure during failure | 15.3% | 14.4% | -0.9 pp |
| 1 | Episode length | 56.15 | 56.65 | +0.50 |
| 2 | Task success | 0.0% | 100.0% | +100.0 pp |
| 2 | Post-failure chain recovered | 0.0% | 100.0% | +100.0 pp |
| 2 | Timeout | 100.0% | 0.0% | -100.0 pp |
| 2 | Restricted mean recovery steps | 220.00 | 5.40 | -214.60 |
| 2 | Tracking during failure | 0.8% | 100.0% | +99.2 pp |
| 2 | Connectivity during failure | 4.8% | 33.0% | +28.1 pp |
| 2 | Chain closure during failure | 0.0% | 16.1% | +16.1 pp |
| 2 | Episode length | 260.00 | 45.40 | -214.60 |

## Interpretation

The three-seed development data can support engineering decisions, but it is not yet a final paper-level estimate. The seed-aware confidence intervals should be treated as a guardrail against overclaiming; the final main table should be rerun with at least five independent training seeds after the baseline set is frozen.
