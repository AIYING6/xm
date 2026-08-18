# TCR/SPC Phase-C v2 Reanalysis Report

Final decision: PHASE-C-V2 GO

This is a zero-training reanalysis of the existing Phase-C 1M evaluation evidence. It does not rewrite the historical v1 result. The historical Phase-C v1 conclusion remains permanently TECHNICAL_INVALID under the v1 all-episode exposure gate. Under the frozen v2 risk-set definition, technical validity passes and the pre-registered TCR stability logic is re-applied unchanged.

## 1. Scope and provenance

- Source: raw_episode_metrics.csv from the archived Phase-C 1M final-checkpoint evaluation.
- Raw records: 18,000 (1,500 nominal + 16,500 failure). No evaluator was rerun; no training, checkpoint, algorithm, environment, reward, PPO, projection, held-out, or canonical seed was changed.
- Evaluation tape hash: 56adbdc2fda3faf14decd94b45cae9a0b6178760725a6fec391ad671e8a30b65.
- Methods: UTR-SG, SPC-SG, TCR-SG; development seeds: 2002, 2101, 2102, 2103, 2104.
- Failure conditions: 11 conditions, 100 episodes each per method/seed.

## 2. Raw-data sufficiency audit

The raw data are sufficient for the requested v2 reanalysis. The 25-column schema contains method, training seed, topology condition, onset, duration, terminal step, failure exposure, return, success, collision, timeout, constraint, and topology/path telemetry. termination_reason is derived from the mutually exclusive terminal flags and terminal step; failure_triggered and failure_active_ever are mapped to failure_exposed according to the frozen evaluator contract. Therefore no field is missing in a way that requires rerunning evaluation.

| Quantity | Result |
| --- | --- |
| Raw row count | 18,000 / 18,000 |
| Failure rows | 16,500 / 16,500 |
| Nominal rows | 1,500 / 1,500 |
| Onset/duration | Present for every failure row |
| Terminal step and terminal flags | Present |
| Return and original safety metrics | Present |
| Risk-set membership | Computed as terminal_step >= scheduled onset |
| Failure trigger status | Computed from failure_exposed within the risk set |

## 3. Frozen v2 definitions

For each method x seed x failure condition, the risk set is R = episodes with terminal_step >= scheduled onset. Technical trigger validity is triggered failures divided by the risk-set size. An episode that collides before onset remains a valid policy outcome, is not exposed, and is not deleted or censored from any overall metric. It is reported separately as pre-trigger termination/collision.

The v2 technical-validity result is PASS: every one of the 165 method x seed x condition cells has a non-empty risk set and a 1.000000 trigger-success rate among that risk set.

## 4. Method x seed results

| Method | Seed | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | collision_F | timeout_F | constraint_F | pre-trigger | survival | |R| | trigger validity |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| utr_sg | 2002 | 101.645 | 90.564 | 91.403 | 77.395 | 0.0373 | 0.9155 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| utr_sg | 2101 | 72.255 | 46.597 | 42.341 | 34.690 | 0.0000 | 1.0000 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| utr_sg | 2102 | 83.327 | 41.200 | 44.333 | 38.138 | 0.0155 | 0.9809 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| utr_sg | 2103 | 72.802 | 56.888 | 58.101 | 55.031 | 0.0000 | 0.8491 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| utr_sg | 2104 | 76.589 | 73.762 | 74.884 | 67.884 | 0.0491 | 0.9509 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| spc_sg | 2002 | 121.742 | 33.723 | 59.667 | 30.364 | 0.0000 | 0.9118 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| spc_sg | 2101 | 100.110 | 84.133 | 81.634 | 78.931 | 0.0000 | 0.9964 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| spc_sg | 2102 | 94.688 | 96.666 | 95.376 | 93.350 | 0.0982 | 0.7455 | 0.0000 | 49 | 95.55% | 1051 | 1.000000 |
| spc_sg | 2103 | 74.470 | 85.325 | 85.087 | 80.109 | 0.0127 | 0.9873 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| spc_sg | 2104 | 109.514 | 99.372 | 93.235 | 81.662 | 0.1600 | 0.8127 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| tcr_sg | 2002 | 76.421 | 118.005 | 113.511 | 104.577 | 0.0336 | 0.9218 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| tcr_sg | 2101 | 107.766 | 105.851 | 102.852 | 88.789 | 0.0000 | 0.9573 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| tcr_sg | 2102 | 94.874 | 73.508 | 70.718 | 62.520 | 0.1555 | 0.8445 | 0.0000 | 0 | 100.00% | 1100 | 1.000000 |
| tcr_sg | 2103 | 130.859 | 119.979 | 116.468 | 107.677 | 0.1555 | 0.7191 | 0.0000 | 12 | 98.91% | 1088 | 1.000000 |
| tcr_sg | 2104 | 140.176 | 138.346 | 134.637 | 124.353 | 0.1427 | 0.6809 | 0.0000 | 8 | 99.27% | 1092 | 1.000000 |

## 5. Pooled descriptive metrics

| Method | J_nominal | J_F0 | J_OOD_mean | J_OOD_worst | collision_F | timeout_F | constraint_F | all-exp | pre-trigger | survival | risk-set trigger |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| utr_sg | 81.324 | 61.802 | 62.212 | 54.628 | 0.0204 | 0.9393 | 0.0000 | 1.000000 | 0.0 | 100.00% | 1.000000 |
| spc_sg | 100.105 | 79.844 | 83.000 | 72.883 | 0.0542 | 0.8907 | 0.0000 | 0.991091 | 9.8 | 99.11% | 1.000000 |
| tcr_sg | 110.019 | 111.138 | 107.637 | 97.583 | 0.0975 | 0.8247 | 0.0000 | 0.996364 | 4.0 | 99.64% | 1.000000 |

All-episode exposure remains reported descriptively. Across all 15 cells, the 69 pre-trigger terminations are exactly the previously audited natural pre-trigger collisions: SPC/seed2002 = 49, TCR/seed2103 = 12, TCR/seed2104 = 8. No evaluator/trigger defect was found.

## 6. Per-condition risk-set technical validity

The following table reports every method x seed x failure condition. risk/100 is the alive-at-onset risk-set size; triggered/risk is the v2 trigger-validity numerator/denominator; pre is the number of pre-onset terminations; all-exp is retained only as the descriptive original metric; J_all and J_risk are the condition return over all episodes and risk-set episodes respectively.

| Method | Seed | Condition | onset/dur | risk/100 | triggered/risk | rate | pre | all-exp | J_all | J_risk |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| utr_sg | 2002 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 90.564 | 90.564 |
| utr_sg | 2002 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 77.395 | 77.395 |
| utr_sg | 2002 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 84.731 | 84.731 |
| utr_sg | 2002 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 95.459 | 95.459 |
| utr_sg | 2002 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 97.020 | 97.020 |
| utr_sg | 2002 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 104.810 | 104.810 |
| utr_sg | 2002 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 79.148 | 79.148 |
| utr_sg | 2002 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 93.523 | 93.523 |
| utr_sg | 2002 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 94.200 | 94.200 |
| utr_sg | 2002 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 90.898 | 90.898 |
| utr_sg | 2002 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 96.848 | 96.848 |
| utr_sg | 2101 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 46.597 | 46.597 |
| utr_sg | 2101 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 38.804 | 38.804 |
| utr_sg | 2101 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 39.876 | 39.876 |
| utr_sg | 2101 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 43.545 | 43.545 |
| utr_sg | 2101 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 42.278 | 42.278 |
| utr_sg | 2101 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 59.308 | 59.308 |
| utr_sg | 2101 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 54.458 | 54.458 |
| utr_sg | 2101 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 37.288 | 37.288 |
| utr_sg | 2101 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 35.049 | 35.049 |
| utr_sg | 2101 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 34.690 | 34.690 |
| utr_sg | 2101 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 38.118 | 38.118 |
| utr_sg | 2102 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 41.200 | 41.200 |
| utr_sg | 2102 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 40.227 | 40.227 |
| utr_sg | 2102 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 39.407 | 39.407 |
| utr_sg | 2102 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 41.030 | 41.030 |
| utr_sg | 2102 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 42.590 | 42.590 |
| utr_sg | 2102 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 72.489 | 72.489 |
| utr_sg | 2102 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 51.808 | 51.808 |
| utr_sg | 2102 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 39.863 | 39.863 |
| utr_sg | 2102 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 38.201 | 38.201 |
| utr_sg | 2102 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 38.138 | 38.138 |
| utr_sg | 2102 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 39.575 | 39.575 |
| utr_sg | 2103 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 56.888 | 56.888 |
| utr_sg | 2103 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 57.366 | 57.366 |
| utr_sg | 2103 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 55.523 | 55.523 |
| utr_sg | 2103 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 58.793 | 58.793 |
| utr_sg | 2103 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 60.198 | 60.198 |
| utr_sg | 2103 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 65.956 | 65.956 |
| utr_sg | 2103 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 57.199 | 57.199 |
| utr_sg | 2103 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 56.452 | 56.452 |
| utr_sg | 2103 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 55.031 | 55.031 |
| utr_sg | 2103 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 57.219 | 57.219 |
| utr_sg | 2103 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 57.269 | 57.269 |
| utr_sg | 2104 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 73.762 | 73.762 |
| utr_sg | 2104 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 67.884 | 67.884 |
| utr_sg | 2104 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 69.232 | 69.232 |
| utr_sg | 2104 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 77.951 | 77.951 |
| utr_sg | 2104 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 83.437 | 83.437 |
| utr_sg | 2104 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 73.023 | 73.023 |
| utr_sg | 2104 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 71.491 | 71.491 |
| utr_sg | 2104 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 79.547 | 79.547 |
| utr_sg | 2104 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 74.553 | 74.553 |
| utr_sg | 2104 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 76.893 | 76.893 |
| utr_sg | 2104 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 74.825 | 74.825 |
| spc_sg | 2002 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 33.723 | 33.723 |
| spc_sg | 2002 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 68.842 | 68.842 |
| spc_sg | 2002 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 67.449 | 67.449 |
| spc_sg | 2002 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 79.521 | 79.521 |
| spc_sg | 2002 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 85.683 | 85.683 |
| spc_sg | 2002 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 49.778 | 49.778 |
| spc_sg | 2002 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 42.975 | 42.975 |
| spc_sg | 2002 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 32.158 | 32.158 |
| spc_sg | 2002 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 30.364 | 30.364 |
| spc_sg | 2002 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 62.110 | 62.110 |
| spc_sg | 2002 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 77.784 | 77.784 |
| spc_sg | 2101 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 84.133 | 84.133 |
| spc_sg | 2101 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 79.100 | 79.100 |
| spc_sg | 2101 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 81.127 | 81.127 |
| spc_sg | 2101 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 83.636 | 83.636 |
| spc_sg | 2101 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 83.944 | 83.944 |
| spc_sg | 2101 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 81.616 | 81.616 |
| spc_sg | 2101 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 85.956 | 85.956 |
| spc_sg | 2101 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 81.596 | 81.596 |
| spc_sg | 2101 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 80.403 | 80.403 |
| spc_sg | 2101 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 80.029 | 80.029 |
| spc_sg | 2101 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 78.931 | 78.931 |
| spc_sg | 2102 | f0_seen_44_80 | 44/80 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 96.666 | 101.186 |
| spc_sg | 2102 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 97.437 | 97.437 |
| spc_sg | 2102 | timing_36_80 | 36/80 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 95.419 | 99.874 |
| spc_sg | 2102 | timing_52_80 | 52/80 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 95.562 | 100.025 |
| spc_sg | 2102 | timing_60_80 | 60/80 | 93/100 | 93/93 | 1.000000 | 7 | 0.9300 | 95.518 | 101.660 |
| spc_sg | 2102 | duration_44_40 | 44/40 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 97.492 | 102.056 |
| spc_sg | 2102 | duration_44_60 | 44/60 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 96.485 | 100.996 |
| spc_sg | 2102 | duration_44_100 | 44/100 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 95.103 | 99.541 |
| spc_sg | 2102 | duration_44_120 | 44/120 | 95/100 | 95/95 | 1.000000 | 5 | 0.9500 | 93.447 | 97.798 |
| spc_sg | 2102 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 93.948 | 93.948 |
| spc_sg | 2102 | compound_60_120 | 60/120 | 93/100 | 93/93 | 1.000000 | 7 | 0.9300 | 93.350 | 99.329 |
| spc_sg | 2103 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 85.325 | 85.325 |
| spc_sg | 2103 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 80.109 | 80.109 |
| spc_sg | 2103 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 82.196 | 82.196 |
| spc_sg | 2103 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 86.884 | 86.884 |
| spc_sg | 2103 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 89.832 | 89.832 |
| spc_sg | 2103 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 85.284 | 85.284 |
| spc_sg | 2103 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 81.391 | 81.391 |
| spc_sg | 2103 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 86.678 | 86.678 |
| spc_sg | 2103 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 86.932 | 86.932 |
| spc_sg | 2103 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 82.060 | 82.060 |
| spc_sg | 2103 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 89.511 | 89.511 |
| spc_sg | 2104 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 99.372 | 99.372 |
| spc_sg | 2104 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 92.532 | 92.532 |
| spc_sg | 2104 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 96.597 | 96.597 |
| spc_sg | 2104 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 96.095 | 96.095 |
| spc_sg | 2104 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 96.992 | 96.992 |
| spc_sg | 2104 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 106.480 | 106.480 |
| spc_sg | 2104 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 100.420 | 100.420 |
| spc_sg | 2104 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 89.477 | 89.477 |
| spc_sg | 2104 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 85.003 | 85.003 |
| spc_sg | 2104 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 81.662 | 81.662 |
| spc_sg | 2104 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 87.095 | 87.095 |
| tcr_sg | 2002 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 118.005 | 118.005 |
| tcr_sg | 2002 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 115.421 | 115.421 |
| tcr_sg | 2002 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 117.500 | 117.500 |
| tcr_sg | 2002 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 117.286 | 117.286 |
| tcr_sg | 2002 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 114.104 | 114.104 |
| tcr_sg | 2002 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 118.413 | 118.413 |
| tcr_sg | 2002 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 120.056 | 120.056 |
| tcr_sg | 2002 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 113.667 | 113.667 |
| tcr_sg | 2002 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 107.059 | 107.059 |
| tcr_sg | 2002 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 107.026 | 107.026 |
| tcr_sg | 2002 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 104.577 | 104.577 |
| tcr_sg | 2101 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 105.851 | 105.851 |
| tcr_sg | 2101 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 109.538 | 109.538 |
| tcr_sg | 2101 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 106.074 | 106.074 |
| tcr_sg | 2101 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 104.953 | 104.953 |
| tcr_sg | 2101 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 105.389 | 105.389 |
| tcr_sg | 2101 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 113.132 | 113.132 |
| tcr_sg | 2101 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 113.799 | 113.799 |
| tcr_sg | 2101 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 100.032 | 100.032 |
| tcr_sg | 2101 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 93.093 | 93.093 |
| tcr_sg | 2101 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 93.723 | 93.723 |
| tcr_sg | 2101 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 88.789 | 88.789 |
| tcr_sg | 2102 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 73.508 | 73.508 |
| tcr_sg | 2102 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 73.761 | 73.761 |
| tcr_sg | 2102 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 73.455 | 73.455 |
| tcr_sg | 2102 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 72.216 | 72.216 |
| tcr_sg | 2102 | timing_60_80 | 60/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 69.643 | 69.643 |
| tcr_sg | 2102 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 88.665 | 88.665 |
| tcr_sg | 2102 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 75.213 | 75.213 |
| tcr_sg | 2102 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 66.249 | 66.249 |
| tcr_sg | 2102 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 62.855 | 62.855 |
| tcr_sg | 2102 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 62.520 | 62.520 |
| tcr_sg | 2102 | compound_60_120 | 60/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 62.600 | 62.600 |
| tcr_sg | 2103 | f0_seen_44_80 | 44/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 119.979 | 119.979 |
| tcr_sg | 2103 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 120.379 | 120.379 |
| tcr_sg | 2103 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 119.415 | 119.415 |
| tcr_sg | 2103 | timing_52_80 | 52/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 116.117 | 116.117 |
| tcr_sg | 2103 | timing_60_80 | 60/80 | 94/100 | 94/94 | 1.000000 | 6 | 0.9400 | 116.351 | 122.295 |
| tcr_sg | 2103 | duration_44_40 | 44/40 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 128.774 | 128.774 |
| tcr_sg | 2103 | duration_44_60 | 44/60 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 124.957 | 124.957 |
| tcr_sg | 2103 | duration_44_100 | 44/100 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 113.956 | 113.956 |
| tcr_sg | 2103 | duration_44_120 | 44/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 108.761 | 108.761 |
| tcr_sg | 2103 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 108.295 | 108.295 |
| tcr_sg | 2103 | compound_60_120 | 60/120 | 94/100 | 94/94 | 1.000000 | 6 | 0.9400 | 107.677 | 113.067 |
| tcr_sg | 2104 | f0_seen_44_80 | 44/80 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 138.346 | 139.468 |
| tcr_sg | 2104 | timing_28_80 | 28/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 138.755 | 138.755 |
| tcr_sg | 2104 | timing_36_80 | 36/80 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 136.650 | 136.650 |
| tcr_sg | 2104 | timing_52_80 | 52/80 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 135.406 | 136.498 |
| tcr_sg | 2104 | timing_60_80 | 60/80 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 130.522 | 131.565 |
| tcr_sg | 2104 | duration_44_40 | 44/40 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 137.205 | 138.315 |
| tcr_sg | 2104 | duration_44_60 | 44/60 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 140.529 | 141.673 |
| tcr_sg | 2104 | duration_44_100 | 44/100 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 136.980 | 138.088 |
| tcr_sg | 2104 | duration_44_120 | 44/120 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 134.188 | 135.268 |
| tcr_sg | 2104 | compound_28_120 | 28/120 | 100/100 | 100/100 | 1.000000 | 0 | 1.0000 | 131.787 | 131.787 |
| tcr_sg | 2104 | compound_60_120 | 60/120 | 99/100 | 99/99 | 1.000000 | 1 | 0.9900 | 124.353 | 125.333 |

## 7. Reapplication of frozen Phase-C stability logic

### 7.1 Catastrophic-seed rule

| Candidate | Seed | F0 ratio vs UTR | OOD-worst ratio vs UTR | timeout diff | catastrophic |
| --- | --- | ---: | ---: | ---: | --- |
| spc_sg | 2002 | 0.3724 | 0.3923 | -0.0036 | YES |
| spc_sg | 2101 | 1.8055 | 2.2753 | -0.0036 | NO |
| spc_sg | 2102 | 2.3462 | 2.4477 | -0.2355 | NO |
| spc_sg | 2103 | 1.4999 | 1.4557 | 0.1382 | NO |
| spc_sg | 2104 | 1.3472 | 1.2030 | -0.1382 | NO |
| tcr_sg | 2002 | 1.3030 | 1.3512 | 0.0064 | NO |
| tcr_sg | 2101 | 2.2716 | 2.5595 | -0.0427 | NO |
| tcr_sg | 2102 | 1.7842 | 1.6393 | -0.1364 | NO |
| tcr_sg | 2103 | 2.1090 | 1.9566 | -0.1300 | NO |
| tcr_sg | 2104 | 1.8756 | 1.8318 | -0.2700 | NO |

- TCR catastrophic seeds: 0/5.
- SPC control catastrophic seeds: 1/5 (seed2002). This is reported as a control diagnostic and does not rewrite the TCR route or the historical v1 result.

### 7.2 TCR OOD-worst direction relative to UTR

| Seed | TCR OOD-worst - UTR OOD-worst | Direction |
| --- | ---: | --- |
| 2002 | 27.182 | positive |
| 2101 | 54.098 | positive |
| 2102 | 24.382 | positive |
| 2103 | 52.646 | positive |
| 2104 | 56.468 | positive |

- TCR is positive on 5/5 seeds.
- SPC is positive on 4/5 seeds; SPC/seed2002 is negative.
- TCR/seed2002 is stable and non-catastrophic: F0 ratio 1.3030, OOD-worst ratio 1.3512.

### 7.3 Pooled comparisons and safety

- TCR pooled minus UTR: J_nominal = 28.696, J_F0 = 49.336, J_OOD_mean = 45.425, J_OOD_worst = 42.955.
- TCR pooled safety: collision 0.0975, timeout 0.8247, constraint 0.0000.
- The frozen systemic-safety erosion rule is not triggered for TCR: constraint violation is zero and timeout is not worse by more than 0.05 in at least three seeds.
- No cross-seed bifurcation rule is triggered: TCR OOD-worst range is 61.833 versus UTR range 42.705, and the frozen two-times-range plus two-times-SD condition is false.

## 8. Asymmetric-anchor diagnostic

The pooled TCR result is better than UTR and better than SPC on J_OOD_mean and J_OOD_worst; TCR is better than SPC on OOD-worst in 4/5 seeds. This supports continued validation of the asymmetric nominal-anchor hypothesis under the pre-registered interpretation. It is not a final paper claim, and it does not establish asymmetric-anchor superiority over all gradient-surgery alternatives.

## 9. Final v2 decision

- Technical validity: PASS under the risk-set trigger-validity definition.
- Pre-trigger episodes: retained in overall returns and safety; separately reported.
- TCR catastrophic seeds: 0/5.
- TCR OOD-worst positive direction: 5/5.
- TCR seed2002: not catastrophic and stable under the frozen rules.
- TCR safety/exposure/constraint requirements: PASS.
- Final decision: PHASE-C-V2 GO.

Under the authorization boundary, this means only:

> Eligible for separately authorized strict-continuous 1M->3M development continuation.

No 3M continuation, held-out, canonical, new training, or method change was started by this reanalysis. The historical Phase-C v1 TECHNICAL_INVALID conclusion remains unchanged and permanently preserved.
