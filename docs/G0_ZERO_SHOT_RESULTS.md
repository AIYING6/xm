# G0 zero-shot results

## Status

This is a frozen-policy, development-only evaluation. No optimizer, rollout update, checkpoint promotion, or training step was executed. The raw evidence contains 5000 episode records, aggregated into 100 method×training-seed×condition records and 30 method×condition summaries.

The primary method is UTR-SG-MAPPO with the five clean T1 development seeds. Historical DRTP checkpoints are reported separately by contract and are not pooled into the primary decision.

## UTR-SG-MAPPO

| condition | family | seeds | J | seed SD | collision | timeout | constraint |
|---|---|---|---|---|---|---|---|
| U1_scout_node_failure | structural_ood | 5 | 90.126 | 41.513 | 0.052 | 0.880 | 0.000 |
| U2_static_symmetric_direct_prune | structural_ood | 5 | 98.982 | 46.860 | 0.012 | 0.932 | 0.000 |
| U3_static_directed_scout_to_attacker_prune | structural_ood | 5 | 107.030 | 47.292 | 0.012 | 0.936 | 0.000 |
| U4_scout_failure_symmetric_direct_prune | structural_ood | 5 | 78.430 | 36.507 | 0.024 | 0.916 | 0.000 |
| U5_relay_failure_directed_direct_prune | structural_ood | 5 | 85.376 | 49.176 | 0.000 | 0.920 | 0.000 |
| U6_relay_failure_symmetric_direct_prune | structural_ood_diagnostic | 5 | 74.733 | 41.744 | 0.000 | 0.920 | 0.000 |
| parameter_duration_44_140 | parameter_ood | 5 | 88.565 | 50.355 | 0.020 | 0.904 | 0.000 |
| parameter_timing_20_80 | parameter_ood | 5 | 89.129 | 47.823 | 0.008 | 0.940 | 0.000 |
| reference_nominal | reference | 5 | 113.516 | 47.673 | 0.016 | 0.952 | 0.000 |
| seen_f0_44_80 | seen_relay_failure | 5 | 91.552 | 49.468 | 0.024 | 0.904 | 0.000 |

## DRTP-SG-MAPPO (descriptive, contract-separated)

| condition | family | seeds | J | seed SD | collision | timeout | constraint |
|---|---|---|---|---|---|---|---|
| U1_scout_node_failure | structural_ood | 3 | 198.950 | 41.864 | 0.013 | 0.667 | 0.000 |
| U2_static_symmetric_direct_prune | structural_ood | 3 | 202.377 | 49.828 | 0.013 | 0.767 | 0.000 |
| U3_static_directed_scout_to_attacker_prune | structural_ood | 3 | 209.236 | 51.062 | 0.013 | 0.753 | 0.000 |
| U4_scout_failure_symmetric_direct_prune | structural_ood | 3 | 187.163 | 45.694 | 0.013 | 0.733 | 0.000 |
| U5_relay_failure_directed_direct_prune | structural_ood | 3 | 171.857 | 82.526 | 0.013 | 0.707 | 0.000 |
| U6_relay_failure_symmetric_direct_prune | structural_ood_diagnostic | 3 | 165.038 | 80.463 | 0.013 | 0.727 | 0.000 |
| parameter_duration_44_140 | parameter_ood | 3 | 154.013 | 68.497 | 0.013 | 0.727 | 0.000 |
| parameter_timing_20_80 | parameter_ood | 3 | 159.926 | 66.440 | 0.020 | 0.827 | 0.000 |
| reference_nominal | reference | 3 | 227.690 | 38.092 | 0.013 | 0.700 | 0.000 |
| seen_f0_44_80 | seen_relay_failure | 3 | 169.099 | 71.625 | 0.013 | 0.753 | 0.000 |
| U1_scout_node_failure | structural_ood | 2 | 135.146 | 71.622 | 0.000 | 0.770 | 0.000 |
| U2_static_symmetric_direct_prune | structural_ood | 2 | 165.969 | 52.884 | 0.000 | 0.730 | 0.000 |
| U3_static_directed_scout_to_attacker_prune | structural_ood | 2 | 170.970 | 53.731 | 0.000 | 0.750 | 0.000 |
| U4_scout_failure_symmetric_direct_prune | structural_ood | 2 | 132.963 | 79.260 | 0.000 | 0.750 | 0.000 |
| U5_relay_failure_directed_direct_prune | structural_ood | 2 | 185.707 | 26.180 | 0.000 | 0.720 | 0.000 |
| U6_relay_failure_symmetric_direct_prune | structural_ood_diagnostic | 2 | 183.290 | 27.977 | 0.000 | 0.680 | 0.000 |
| parameter_duration_44_140 | parameter_ood | 2 | 179.338 | 28.143 | 0.000 | 0.600 | 0.000 |
| parameter_timing_20_80 | parameter_ood | 2 | 180.662 | 44.843 | 0.000 | 0.690 | 0.000 |
| reference_nominal | reference | 2 | 213.243 | 26.311 | 0.000 | 0.520 | 0.000 |
| seen_f0_44_80 | seen_relay_failure | 2 | 181.004 | 29.016 | 0.010 | 0.720 | 0.000 |

## Risk-set validity and safety diagnostics

For every failure condition, the report retains all episodes in unconditional return and safety metrics. Trigger validity is reported among episodes alive at the scheduled onset. Pre-trigger termination is a policy outcome, not an evaluator failure. The machine-readable seed table contains `failure_exposure_all_episodes`, `survival_to_onset_fraction`, `trigger_success_among_risk_set`, and `pre_trigger_collision` for every cell.

## Provenance

- Topology manifest: `artifacts/g0/topology_manifest.json`
- Episode-level evidence: `artifacts/g0/g0_episode_results.csv`
- Seed-level evidence: `artifacts/g0/seed_topology_results.csv`
- Pooled condition evidence: `artifacts/g0/topology_results.csv`
- Summary: `artifacts/g0/generalization_summary.json`
- Figures: `artifacts/g0/figures/`
