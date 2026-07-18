# Strict-Sensing Formal Development Summary

Generated: 2026-07-17T00:56:29

This is a three-seed development result for the formal strict-sensing relay-failure protocol. It uses validation-selected checkpoints and disjoint test episodes. It is stronger than the earlier 10-update pilot, but it is still a development result until the final seed budget and baseline set are frozen.

## Protocol

```text
seeds = [0, 1, 2]
scenario = relay_failure
strict_target_sensing = True
validation episodes per seed/checkpoint = 50
test episodes per selected seed/checkpoint = 100
checkpoint snapshots = every 10 updates up to 120
checkpoint selection = validation recovery/success/recovery-step score
```

## Test Summary

| Graph | Seeds | Recovery % mean/std | Success % mean/std | Recovery steps mean/std | Timeout % mean/std |
| --- | ---: | ---: | ---: | ---: | ---: |
| `single` | 3 | 92.7 / 6.4 | 92.7 / 6.4 | 5.39 / 0.11 | 7.3 / 6.4 |
| `multi_relation` | 3 | 100.0 / 0.0 | 100.0 / 0.0 | 5.43 / 0.15 | 0.0 / 0.0 |

## Paired Delta

Positive recovery/success deltas favor the multi-relation model. Negative step/timeout deltas favor the multi-relation model.

| Metric | Mean delta | Std over seeds |
| --- | ---: | ---: |
| Recovery probability | +7.3 pp | 6.4 pp |
| Success probability | +7.3 pp | 6.4 pp |
| Recovery steps | +0.05 | 0.21 |
| Timeout probability | -7.3 pp | 6.4 pp |

## Selected Checkpoints and Seed-Level Test Results

| Seed | Graph | Update | Recovery % | Success % | Recovery steps | Timeout % |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | `multi_relation` | 30 | 100.0 | 100.0 | 5.52 | 0.0 |
| 0 | `single` | 70 | 90.0 | 90.0 | 5.48 | 10.0 |
| 1 | `multi_relation` | 110 | 100.0 | 100.0 | 5.26 | 0.0 |
| 1 | `single` | 10 | 88.0 | 88.0 | 5.42 | 12.0 |
| 2 | `multi_relation` | 30 | 100.0 | 100.0 | 5.52 | 0.0 |
| 2 | `single` | 70 | 100.0 | 100.0 | 5.26 | 0.0 |

## Seed-Level Paired Deltas

| Seed | Recovery delta pp | Success delta pp | Recovery-step delta | Timeout delta pp |
| ---: | ---: | ---: | ---: | ---: |
| 0 | +10.0 | +10.0 | +0.04 | -10.0 |
| 1 | +12.0 | +12.0 | -0.16 | -12.0 |
| 2 | +0.0 | +0.0 | +0.26 | +0.0 |

## Interpretation

- This development run supports continuing the strict-sensing relay-failure line.
- The validation-selected multi-relation checkpoints are consistently strong across seeds.
- The single-graph baseline can also solve some seeds after validation selection, so the final paper still needs five seeds, fair MAPPO/GAT baselines, and seed-aware statistics before making a final Q2-level claim.

## Files

- `results/intercept_3d_strict_sensing_formal_dev_summary.csv`