# Strict-Sensing Radar-0.10 Relay-Failure Probe Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_radar010_relay_probe`

This is a diagnostic-only evaluation. It reuses validation-selected 30-update straight-target checkpoints and evaluates them under `radar_dropout_prob=0.10`, `relay_failure`, and `strict_target_sensing`. No retraining was performed.

| Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_relation | 3 | 93.3% | 93.3% | 5.86 | 84.5% | 42.8% | 6.7% |
| single | 3 | 95.0% | 95.0% | 5.50 | 85.0% | 43.5% | 5.0% |
| no_graph | 3 | 40.0% | 40.0% | 10.32 | 25.4% | 20.9% | 60.0% |

## Interpretation

Radar dropout 0.10 does not strengthen the `multi_relation` over `single` claim in this checkpoint-only probe. `single` is slightly higher on success/recovery, and the seed-aware delta for `multi_relation - single` is centered near zero. The setting still separates graph policies from `no_graph` on tracking and recovery, but it should not be used as evidence that the multi-relation encoder is universally better under all sensing perturbations.
