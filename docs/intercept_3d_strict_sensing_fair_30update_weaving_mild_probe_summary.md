# Strict-Sensing Weaving-Mild Probe Summary

Result directory: `results/intercept_3d_strict_sensing_fair_30update_weaving_mild_probe`

This is a diagnostic-only evaluation. It reuses validation-selected 30-update straight-target checkpoints and evaluates them under `target_policy=weaving_mild`, `relay_failure`, and `strict_target_sensing`. No retraining was performed.

| Method | Seeds | Success | Recovery | Recovery steps | Tracking | Connectivity | Timeout |
|---|---:|---:|---:|---:|---:|---:|---:|
| multi_relation | 3 | 6.7% | 6.7% | 122.00 | 31.5% | 13.2% | 93.3% |
| single | 3 | 0.0% | 0.0% | inf | 28.2% | 15.4% | 100.0% |
| no_graph | 3 | 0.0% | 0.0% | inf | 5.2% | 7.2% | 100.0% |

## Interpretation

`weaving_mild` is too hard for the current straight-target-trained checkpoints. It collapses `single` and `no_graph` to zero recovery and also leaves `multi_relation` at very low absolute recovery. This probe should not be promoted as the current main experiment. It indicates that maneuvering-target results need a staged maneuvering curriculum or a milder intermediate scenario before paper-facing use.