# Strict-Sensing Range-0.75 Relay-Failure Probe Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_range075_relay_probe`

This is a diagnostic-only evaluation. It reuses validation-selected 30-update straight-target checkpoints and evaluates them under `communication_range_scale=0.75`, `relay_failure`, and `strict_target_sensing`. No retraining was performed.

| Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_relation | 3 | 98.3% | 98.3% | 6.00 | 98.6% | 19.7% | 1.7% |
| single | 3 | 96.7% | 96.7% | 5.39 | 97.0% | 37.5% | 3.3% |
| no_graph | 3 | 38.3% | 38.3% | 4.92 | 27.5% | 20.0% | 61.7% |

## Interpretation

Range 0.75 is not a useful discriminator for `single` versus `multi_relation` in this checkpoint-only probe. It keeps both graph methods near saturation while preserving the large gap against `no_graph`. This setting can support the claim that graph/message structure is necessary, but it does not strengthen the multi-relation-over-single claim. A better next probe should modify the sensing/target-information dependency rather than only shrinking communication range.
